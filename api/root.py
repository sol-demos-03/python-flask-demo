"""Application root"""
import os
import math
from flask import Blueprint
from flask_json import json_response
from uptime import uptime

BP = Blueprint('root', __name__)

@BP.route('/')
@BP.route('/status')
def root():
    """Root endpoint"""
    name = os.environ.get('APPLICATION_NAME')
    version = os.environ.get('APPLICATION_VERSION')
    environment_name = os.environ.get("ENVIRONMENT_NAME")

    # do some cpu intensive computation
    _x = 0.0001
    for _ in range(0, 1000000):
        _x = _x + math.sqrt(_x)

    return json_response(
        200,
        name=name,
        version=version,
        uptime=uptime(),
        environment_name=environment_name,
    )
