FROM python:3.7

ENV APP_HOME /app
WORKDIR $APP_HOME

# Copy application files
COPY ./api api
COPY ./setup.cfg .
COPY ./setup.py .
COPY ./README.md .

# Setup
RUN pip install wheel
RUN python setup.py bdist_wheel
RUN pip install dist/python_flask-1.0.0-py3-none-any.whl

ENV FLASK_INSTANCE_DIR_NAME /var/api-instance
RUN mkdir -p $FLASK_INSTANCE_DIR_NAME
RUN python -c 'import os; print("SECRET_KEY =",os.urandom(16))' > $FLASK_INSTANCE_DIR_NAME/config.py

RUN pip install waitress

EXPOSE 8080
ENTRYPOINT ["waitress-serve", "--call", "api:create_app"]
