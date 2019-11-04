import json
import numpy as np
import pandas as pd
import networkx as nx
from networkx.readwrite import json_graph
from flask import Flask, abort, jsonify, request, send_from_directory
from keras.models import Model, load_model
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import hashlib
import logging
import glob
import pickle
from tqdm import tqdm
from joblib import Parallel, delayed
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import numpy.distutils.system_info as sysinfo
auto_threshold = 0
import warnings
warnings.filterwarnings("ignore", category=UserWarning)  #, module='gensim')
import os
import tensorflow as tf
import multiprocessing
from kafka import KafkaConsumer, KafkaProducer
import requests

print("initting tf")

KAFKA_HOST=kafka-swift-ml-ol-kafka.kafka

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

print("loading autoencoder model")

autoencoder = load_model("api/autoencoder.h5")
autoencoder.compile(optimizer='adam',
                    loss='mean_squared_error',
                    metrics=['accuracy'])
autoencoder._make_predict_function()

print("Server Running...")

app = Flask(__name__, static_folder='public')

@app.route('/api/v1/score', methods=['POST'])
def make_score():
    data = request.get_json(force=True)
    graph = load(data)
    # Running the Graph2Vec algorithm unparallelized
    result = runGraph2Vec(graph=graph, min_count=1, n_dims=64, n_workers=1)  # result as a pd dataframe
    result = result.drop(['type'], axis=1)
    with open('api/transformer', 'rb') as handle:
        num_pipeline = pickle.load(handle)
    with open('api/threshold', 'rb') as handle:
        auto_threshold = pickle.load(handle)

    print("Graph embedding:")
    print(result)
    result = num_pipeline.transform(result)
    print("\n")
    print("Scaled embedding:")
    print(result)

    prediction = autoencoder.predict(result)
    mse = np.mean(np.power(result - prediction, 2), axis=1)
    output = []
    for val in mse:
        if val > auto_threshold:
            output.append(1)
        else:
            output.append(0)

    response = app.response_class(
        response=json.dumps(output),
        status=200,
        mimetype='application/json'
    )
    print(response)
    return response

@app.route('/<path:subpath>', methods=['GET'])
def public(subpath):
    #return subpath
    return send_from_directory('public', subpath)

@app.route('/', methods=['GET'])
def root():
    return send_from_directory(app.static_folder, 'index.html')


def load(data):
    G = json_graph.node_link_graph(data)
    return G

def getCCs(G):
    CC_subgraphs= []
    for cc in list(nx.connected_components(G.to_undirected())):
        CC_subgraphs.append(G.subgraph(cc).copy())

    return CC_subgraphs

class WeisfeilerLehmanMachine:
    """
    Weisfeiler Lehman feature extractor class.
    """
    def __init__(self, graph, features, iterations):
        """
        Initialization method which executes feature extraction.
        :param graph: The Nx graph object.
        :param features: Feature hash table.
        :param iterations: Number of WL iterations.
        """
        self.iterations = iterations
        self.graph = graph
        self.features = features
        self.nodes = self.graph.nodes()
        self.extracted_features = [str(v) for k,v in features.items()]
        self.rinse_repeat()

    def iterate(self):
        """
        The method does a single WL recursion.
        :return new_features: The hash table with extracted WL features.
        """
        new_features = {}
        for node in self.nodes:
            nebs = self.graph.neighbors(node)
            degs = [self.features[neb] for neb in nebs]
            features = "_".join([str(self.features[node])]+list(set(sorted([str(deg) for deg in degs]))))
            hash_object = hashlib.md5(features.encode())
            hashing = hash_object.hexdigest()
            new_features[node] = hashing
        self.extracted_features = self.extracted_features + list(new_features.values())
        return new_features

    def rinse_repeat(self):
        """
        The method does a series of WL recursions.
        """
        for iteration in range(self.iterations):
            self.features = self.iterate()

def feature_extractor(index, graph, rounds):
    """
    Function to extract WL features from a graph.
    :param index: The index value of the subgraph
    :param graph: Individual subgraph representing a transaction
    :param rounds: Number of WL iterations.
    :return doc: Document collection object.
    """
    features = graph._node
    machine = WeisfeilerLehmanMachine(graph,features,rounds)
    doc = TaggedDocument(words = machine.extracted_features , tags = ["g_" + str(index)])
    return doc


def ret_embedding(model, ids, dimensions):
    """
    Function to save the embedding.
    :param output_path: Path to the embedding csv.
    :param model: The embedding model object.
    :param ids: The list of subgraph ids.
    :param dimensions: The embedding dimension parameter.
    """
    out = []
    for identifier in ids:
        out.append([identifier] + list(model.docvecs["g_"+str(identifier)]))

    out = pd.DataFrame(out,columns = ["type"] +["x_" +str(dimension) for dimension in range(dimensions)])
    out = out.sort_values(["type"])
    return out


def runGraph2Vec(graph, n_dims=128, n_workers=4, n_epochs=1,
                 min_count=5, wl_iters=2, learning_rate=0.025, sampling_rate=0.0001):
    """
    Execution harness for graph2vec algorithm. Parameter list:
    - n_dims         INT          Number of dimensions.                             Default is 128.
    - n_workers      INT          Number of workers.                                Default is 4.
    - n_epochs       INT          Number of training epochs.                        Default is 1.
    - min_count      INT          Minimal feature count to keep.                    Default is 5.
    - wl_iters       INT          Number of feature extraction recursions.          Default is 2.
    - learning_rate  FLOAT        Initial learning rate.                            Default is 0.025.
    - sampling_rate  FLOAT        Down sampling rate for frequent features.         Default is 0.0001.
    """

    print("\nFeature extraction started.\n")
    # watch out for trouble here
    ConnectedComps = getCCs(graph)
    document_collections = Parallel(n_jobs = n_workers)(delayed(feature_extractor)(i, g, wl_iters) for i, g in tqdm(enumerate(ConnectedComps)))
    print("\nOptimization started.\n")
    model = Doc2Vec(document_collections,
                    vector_size = n_dims,
                    window = 0,
                    min_count = min_count,
                    dm = 0,
                    sample = sampling_rate,
                    workers = n_workers,
                    epochs = n_epochs,
                    alpha = learning_rate)

    subgraph_ids = list(range(len(ConnectedComps)))
    return ret_embedding(model, subgraph_ids, n_dims)

    #TODO: consider adding timing or feedback to track progress of the algorithm

def consumeQueue():
    consumer = KafkaConsumer(bootstrap_servers=KAFKA_HOST)
    consumer.subscribe(['cctxns'])
    producer = KafkaProducer(bootstrap_servers=KAFKA_HOST)
    for msg in consumer:
        r = requests.post('http://127.0.0.1:8080/api/v1/score', data=msg)
        if r.status_code > 199 and r.status_code < 300:
            result = r.json()
            producer.send('ccresults', json.dumps(result))
        else:
            print(f"response returned status code: {r.status_code}")
            print(r.text)

if __name__ == '__main__':
    p = Process(target=consumeQueue,args=())
    p.start()
    app.run(host = "0.0.0.0", port = 8080, debug = True)
