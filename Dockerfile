FROM python:3.7

ENV APP_HOME /app
WORKDIR $APP_HOME

# do this first so we don't keep re-running it when source changes
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./setup.cfg .
COPY ./setup.py .
#COPY ./public public
COPY ./README.md .

# Setup
RUN pip install waitress
RUN pip install wheel
RUN python setup.py bdist_wheel
RUN pip install dist/python_flask-1.0.0-py3-none-any.whl

# Copy application files
COPY ./api api

#ENV FLASK_INSTANCE_DIR_NAME /var/api-instance
#RUN mkdir -p $FLASK_INSTANCE_DIR_NAME
#RUN python -c 'import os; print("SECRET_KEY =",os.urandom(16))' > $FLASK_INSTANCE_DIR_NAME/config.py


EXPOSE 8080
#ENTRYPOINT ["waitress-serve", "--port=8080", "--call", "api:create_app"]
ENTRYPOINT ["python", "api/rest_api.py"]
