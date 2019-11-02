"""API init"""
import os

from flask import Flask

def create_app():
  from .rest_api import app
  return app
