import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'adornsaturn'))

from index import app


def test_login_page():
    client = app.test_client()
    response = client.get('/login')
    assert response.status_code == 200


def test_api_products():
    client = app.test_client()
    response = client.get('/api/products')
    assert response.status_code == 200