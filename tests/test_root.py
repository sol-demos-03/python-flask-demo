import pytest


def test_root(client):
    response = client.get('/')
    assert response.status_code is 200
