"""API init"""
import os

from flask import Flask
from flask_json import FlaskJSON


def create_app(test_config=None):
  from rest_api import app
  return app
