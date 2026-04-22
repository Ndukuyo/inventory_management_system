from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime
from typing import Dict, List, Optional

app = Flask(__name__)
CORS(app)


inventory_db = []
next_id = 1


OPENFOODFACTS_API = "https://world.openfoodfacts.org/api/v0/product/{}.json"
OPENFOODFACTS_SEARCH = "https://world.openfoodfacts.org/cgi/search.pl"

def fetch_product_from_openfoodfacts(barcode: str = None, product_name: str = None) -> Optional[Dict]:

    try:
        if barcode:
        
            response = requests.get(OPENFOODFACTS_API.format(barcode), timeout=10)
            data = response.json()
            
            if data.get('status') == 1 and data.get('product'):
                product = data['product']
                return {
                    'product_name': product.get('product_name', 'Unknown Product'),
                    'brands': product.get('brands', 'Unknown Brand'),
                    'ingredients_text': product.get('ingredients_text', 'No ingredients listed'),
                    'nutriments': product.get('nutriments', {}),
                    'categories': product.get('categories', 'Uncategorized'),
                    'image_url': product.get('image_url', ''),
                    'quantity': product.get('quantity', ''),
                    'origin': product.get('origin', 'Unknown')
                }
        
        elif product_name:
        
            params = {
                'search_terms': product_name,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': 1
            }
            response = requests.get(OPENFOODFACTS_SEARCH, params=params, timeout=10)
            data = response.json()
            
            if data.get('products') and len(data['products']) > 0:
                product = data['products'][0]
                return {
                    'product_name': product.get('product_name', 'Unknown Product'),
                    'brands': product.get('brands', 'Unknown Brand'),
                    'ingredients_text': product.get('ingredients_text', 'No ingredients listed'),
                    'nutriments': product.get('nutriments', {}),
                    'categories': product.get('categories', 'Uncategorized'),
                    'image_url': product.get('image_url', ''),
                    'quantity': product.get('quantity', ''),
                    'origin': product.get('origin', 'Unknown')
                }
        
        return None
    
    except requests.RequestException as e:
        print(f"API Error: {e}")
        return None


@app.route('/inventory', methods=['GET'])
def get_all_items():
    
    return jsonify({
        'success': True,
        'data': inventory_db,
        'count': len(inventory_db)
    }), 200

@app.route('/inventory/<int:item_id>', methods=['GET'])
def get_single_item(item_id: int):
   
    item = next((item for item in inventory_db if item['id'] == item_id), None)
    
    if item:
        return jsonify({
            'success': True,
            'data': item
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': f'Item with ID {item_id} not found'
        }), 404

@app.route('/inventory', methods=['POST'])
def add_item():
  
    global next_id
    
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    if 'name' not in data and 'barcode' not in data and 'product_name' not in data:
        return jsonify({
            'success': False,
            'error': 'Either name, barcode, or product_name is required'
        }), 400
    
    
    external_data = None
    if 'barcode' in data and data['barcode']:
        external_data = fetch_product_from_openfoodfacts(barcode=data['barcode'])
    elif 'product_name' in data and data['product_name']:
        external_data = fetch_product_from_openfoodfacts(product_name=data['product_name'])
    
    
    new_item = {
        'id': next_id,
        'name': data.get('name', external_data.get('product_name') if external_data else 'Unknown Product'),
        'barcode': data.get('barcode', ''),
        'price': float(data.get('price', 0.00)),
        'stock_quantity': int(data.get('stock_quantity', 0)),
        'brand': data.get('brand', external_data.get('brands') if external_data else 'Unknown Brand'),
        'category': data.get('category', external_data.get('categories') if external_data else 'Uncategorized'),
        'description': data.get('description', ''),
        'ingredients': external_data.get('ingredients_text') if external_data else data.get('ingredients', ''),
        'nutritional_info': external_data.get('nutriments') if external_data else {},
        'image_url': external_data.get('image_url') if external_data else '',
        'quantity': external_data.get('quantity') if external_data else data.get('quantity', ''),
        'origin': external_data.get('origin') if external_data else data.get('origin', ''),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    inventory_db.append(new_item)
    next_id += 1
    
    return jsonify({
        'success': True,
        'data': new_item,
        'message': 'Item added successfully'
    }), 201

@app.route('/inventory/<int:item_id>', methods=['PATCH'])
def update_item(item_id: int):
   
    item = next((item for item in inventory_db if item['id'] == item_id), None)
    
    if not item:
        return jsonify({
            'success': False,
            'error': f'Item with ID {item_id} not found'
        }), 404
    
    data = request.get_json()
    
    
    allowed_fields = ['name', 'price', 'stock_quantity', 'brand', 'category', 
                     'description', 'quantity', 'origin']
    
    for field in allowed_fields:
        if field in data:
            if field in ['price', 'stock_quantity']:
                item[field] = float(data[field]) if field == 'price' else int(data[field])
            else:
                item[field] = data[field]
    
    item['updated_at'] = datetime.now().isoformat()
    
    return jsonify({
        'success': True,
        'data': item,
        'message': 'Item updated successfully'
    }), 200

@app.route('/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id: int):
   
    global inventory_db
    
    item = next((item for item in inventory_db if item['id'] == item_id), None)
    
    if not item:
        return jsonify({
            'success': False,
            'error': f'Item with ID {item_id} not found'
        }), 404
    
    inventory_db = [item for item in inventory_db if item['id'] != item_id]
    
    return jsonify({
        'success': True,
        'message': f'Item with ID {item_id} deleted successfully'
    }), 200

@app.route('/inventory/search', methods=['GET'])
def search_inventory():
   
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query required'
        }), 400
    
    results = [item for item in inventory_db 
               if query in item['name'].lower() 
               or query in item['brand'].lower() 
               or query in item['category'].lower()]
    
    return jsonify({
        'success': True,
        'data': results,
        'count': len(results)
    }), 200

@app.route('/inventory/fetch-external', methods=['POST'])
def fetch_external_product():
   
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    barcode = data.get('barcode')
    product_name = data.get('product_name')
    
    if not barcode and not product_name:
        return jsonify({
            'success': False,
            'error': 'Either barcode or product_name is required'
        }), 400
    
    external_data = fetch_product_from_openfoodfacts(barcode=barcode, product_name=product_name)
    
    if external_data:
        return jsonify({
            'success': True,
            'data': external_data
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': 'Product not found in external API'
        }), 404

if __name__ == '__main__':
    
    sample_item = {
        'id': next_id,
        'name': 'Soko Maize Meal',
        'barcode': '123456789012',
        'price': 160,
        'stock_quantity': 50,
        'brand': 'Soko',
        'category': 'Maize Floor',
        'description': 'Make from quality kenyan grain',
        'ingredients': 'Maize',
        'nutritional_info': {'calories': 30, 'protein': '1g'},
        'image_url': 'https://example.com/soko.jpg',
        'quantity': '2kg',
        'origin': 'Kenya',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    inventory_db.append(sample_item)
    next_id += 1
    
    app.run(debug=True, port=5000)
