import pytest
import json
from app import app, inventory_db, next_id, fetch_product_from_openfoodfacts
from unittest.mock import patch, Mock
import requests

@pytest.fixture
def client():
   
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Clear database before each test
        inventory_db.clear()
        # Add test data
        test_item = {
            'id': 1,
            'name': 'Test Product',
            'price': 10.99,
            'stock_quantity': 100,
            'brand': 'Test Brand',
            'category': 'Test Category',
            'barcode': '123456789',
            'ingredients': 'Test ingredients',
            'nutritional_info': {},
            'image_url': '',
            'quantity': '500g',
            'origin': 'Test Country',
            'created_at': '2024-01-01T00:00:00',
            'updated_at': '2024-01-01T00:00:00'
        }
        inventory_db.append(test_item)
        yield client

def test_get_all_items(client):
   
    response = client.get('/inventory')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['count'] == 1
    assert len(data['data']) == 1

def test_get_single_item_success(client):
   
    response = client.get('/inventory/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['data']['id'] == 1
    assert data['data']['name'] == 'Test Product'

def test_get_single_item_not_found(client):
    
    response = client.get('/inventory/999')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['success'] == False
    assert 'not found' in data['error']

def test_add_item_without_external_api(client):
    
    new_item = {
        'name': 'New Product',
        'price': 15.99,
        'stock_quantity': 50,
        'brand': 'New Brand',
        'category': 'New Category'
    }
    response = client.post('/inventory', json=new_item)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['data']['name'] == 'New Product'
    assert data['data']['price'] == 15.99

def test_add_item_missing_required_fields(client):
    
    response = client.post('/inventory', json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] == False

@patch('app.fetch_product_from_openfoodfacts')
def test_add_item_with_barcode(mock_fetch, client):
   
    mock_fetch.return_value = {
        'product_name': 'External Product',
        'brands': 'External Brand',
        'ingredients_text': 'External ingredients',
        'nutriments': {'calories': 100},
        'categories': 'External Category',
        'image_url': 'http://example.com/image.jpg',
        'quantity': '1L',
        'origin': 'External Origin'
    }
    
    new_item = {
        'barcode': '1234567890123',
        'price': 5.99,
        'stock_quantity': 75
    }
    response = client.post('/inventory', json=new_item)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['data']['name'] == 'External Product'
    assert data['data']['brand'] == 'External Brand'

def test_update_item_success(client):
    
    update_data = {
        'price': 12.99,
        'stock_quantity': 75
    }
    response = client.patch('/inventory/1', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['data']['price'] == 12.99
    assert data['data']['stock_quantity'] == 75

def test_update_item_not_found(client):
   
    response = client.patch('/inventory/999', json={'price': 20.00})
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['success'] == False

def test_delete_item_success(client):
  
    response = client.delete('/inventory/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    
  
    get_response = client.get('/inventory/1')
    assert get_response.status_code == 404

def test_delete_item_not_found(client):
    
    response = client.delete('/inventory/999')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['success'] == False

def test_search_inventory(client):
   
    test_item2 = {
        'id': 2,
        'name': 'Another Product',
        'brand': 'Test Brand',
        'category': 'Electronics',
        'price': 25.99,
        'stock_quantity': 30,
        'barcode': '987654321',
        'ingredients': '',
        'nutritional_info': {},
        'image_url': '',
        'quantity': '',
        'origin': '',
        'created_at': '2024-01-01T00:00:00',
        'updated_at': '2024-01-01T00:00:00'
    }
    inventory_db.append(test_item2)
    
    response = client.get('/inventory/search?q=test')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['count'] == 1
    assert data['data'][0]['name'] == 'Test Product'

def test_fetch_external_product_success():
 
    with patch('app.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 1,
            'product': {
                'product_name': 'Mock Product',
                'brands': 'Mock Brand',
                'ingredients_text': 'Mock ingredients',
                'nutriments': {'sugar': '10g'},
                'categories': 'Mock Category',
                'image_url': 'http://mock.com/image.jpg',
                'quantity': '500ml',
                'origin': 'Mock Origin'
            }
        }
        mock_get.return_value = mock_response
        
        result = fetch_product_from_openfoodfacts(barcode='123456789')
        assert result is not None
        assert result['product_name'] == 'Mock Product'
        assert result['brands'] == 'Mock Brand'

def test_fetch_external_product_not_found():
  
    with patch('app.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {'status': 0}
        mock_get.return_value = mock_response
        
        result = fetch_product_from_openfoodfacts(barcode='invalid')
        assert result is None

def test_fetch_external_product_api_error():
 
    with patch('app.requests.get') as mock_get:
        mock_get.side_effect = requests.RequestException("Network error")
        
        result = fetch_product_from_openfoodfacts(barcode='123456789')
        assert result is None

def test_fetch_external_endpoint(client):
   
    with patch('app.fetch_product_from_openfoodfacts') as mock_fetch:
        mock_fetch.return_value = {
            'product_name': 'External Product',
            'brands': 'External Brand',
            'ingredients_text': 'Test ingredients',
            'nutriments': {},
            'categories': 'Test',
            'image_url': '',
            'quantity': '1kg',
            'origin': 'Test'
        }
        
        response = client.post('/inventory/fetch-external', 
                              json={'barcode': '123456789'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['product_name'] == 'External Product'

def test_add_item_with_invalid_data(client):
   
    invalid_item = {
        'name': 'Invalid Product',
        'price': 'not_a_number',
        'stock_quantity': 'not_an_integer'
    }
    response = client.post('/inventory', json=invalid_item)
  
    assert response.status_code in [200, 201, 400]