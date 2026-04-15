#!/usr/bin/env python3
import click
import requests
import json
from typing import Dict, Any

API_BASE_URL = "http://localhost:5000"

class InventoryCLI:
    def __init__(self):
        self.base_url = API_BASE_URL
    
    def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                return {"message": 'Invalid method'}
            
            return response.json()
        
        except requests.ConnectionError:
            return {"message": 'Cannot connect to API. Make sure Flask server is running.'}
        except Exception as e:
            return {"message": str(e)}
    
    def display_item(self, item: Dict):
        
        click.echo("\n")
        click.echo(f"ID: {item['id']}")
        click.echo(f"Name: {item['name']}")
        click.echo(f"Brand: {item['brand']}")
        click.echo(f"Price: ${item['price']:.2f}")
        click.echo(f"Stock: {item['stock_quantity']} units")
        click.echo(f"Category: {item['category']}")
        click.echo(f"Barcode: {item.get('barcode', 'N/A')}")
        click.echo(f"Quantity: {item.get('quantity', 'N/A')}")
        click.echo(f"Origin: {item.get('origin', 'N/A')}")
        click.echo(f"Description: {item.get('description', 'N/A')}")
        click.echo(f"Ingredients: {item.get('ingredients', 'N/A')[:100]}...")
        

@click.group()
def cli():
    
    pass

@cli.command()
def list():
    
    cli_obj = InventoryCLI()
    result = cli_obj.make_request('GET', '/inventory')
    
    if result.get('success'):
        if result['count'] == 0:
            click.echo("No items in inventory.")
        else:
            click.echo(f"\nFound {result['count']} items in inventory:")
            for item in result['data']:
                click.echo(f"  [{item['id']}] {item['name']} - ${item['price']:.2f} (Stock: {item['stock_quantity']})")
    else:
        click.echo(f"Error: {result.get('error', 'Unknown error')}")

@cli.command()
@click.argument('item_id', type=int)
def view(item_id):
    
    cli_obj = InventoryCLI()
    result = cli_obj.make_request('GET', f'/inventory/{item_id}')
    
    if result.get('success'):
        cli_obj.display_item(result['data'])
    else:
        click.echo(f"Error: {result.get('error', 'Item not found')}")

@cli.command()
@click.option('--name', prompt='Product name', help='Product name')
@click.option('--price', prompt='Price', type=float, help='Product price')
@click.option('--stock', prompt='Stock quantity', type=int, help='Initial stock quantity')
@click.option('--brand', prompt='Brand', default='Unknown', help='Product brand')
@click.option('--category', prompt='Category', default='General', help='Product category')
@click.option('--barcode', default='', help='Product barcode (optional)')
def add(name, price, stock, brand, category, barcode):
    
    cli_obj = InventoryCLI()
    
    data = {
        'name': name,
        'price': price,
        'stock_quantity': stock,
        'brand': brand,
        'category': category,
        'barcode': barcode if barcode else None
    }
    
    result = cli_obj.make_request('POST', '/inventory', data)
    
    if result.get('success'):
        click.echo(f"✓ Item added successfully!")
        click.echo(f"  ID: {result['data']['id']}")
        if result['data'].get('ingredients') != '':
            click.echo("  Product details enriched from OpenFoodFacts API")
    else:
        click.echo(f"Error: {result.get('error', 'Failed to add item')}")

@cli.command()
@click.argument('item_id', type=int)
@click.option('--name', help='New product name')
@click.option('--price', type=float, help='New price')
@click.option('--stock', type=int, help='New stock quantity')
@click.option('--brand', help='New brand')
@click.option('--category', help='New category')
def update(item_id, name, price, stock, brand, category):
    
    cli_obj = InventoryCLI()
    
    data = {}
    if name:
        data['name'] = name
    if price is not None:
        data['price'] = price
    if stock is not None:
        data['stock_quantity'] = stock
    if brand:
        data['brand'] = brand
    if category:
        data['category'] = category
    
    if not data:
        click.echo("No update fields provided.")
        return
    
    result = cli_obj.make_request('PATCH', f'/inventory/{item_id}', data)
    
    if result.get('success'):
        click.echo(f"Item {item_id} updated successfully!")
    else:
        click.echo(f"Error: {result.get('error', 'Failed to update item')}")

@cli.command()
@click.argument('item_id', type=int)
def delete(item_id):

    if click.confirm(f"Are you sure you want to delete item {item_id}?"):
        cli_obj = InventoryCLI()
        result = cli_obj.make_request('DELETE', f'/inventory/{item_id}')
        
        if result.get('success'):
            click.echo(f" Item {item_id} deleted successfully!")
        else:
            click.echo(f" Error: {result.get('error', 'Failed to delete item')}")

@cli.command()
@click.option('--barcode', help='Search by barcode')
@click.option('--name', help='Search by product name')
def fetch(barcode, name):
    
    if not barcode and not name:
        click.echo("Please provide either --barcode or --name")
        return
    
    cli_obj = InventoryCLI()
    data = {}
    if barcode:
        data['barcode'] = barcode
    if name:
        data['product_name'] = name
    
    result = cli_obj.make_request('POST', '/inventory/fetch-external', data)
    
    if result.get('success'):
        click.echo("\n Product found on OpenFoodFacts!")
        click.echo("="*50)
        for key, value in result['data'].items():
            if isinstance(value, dict):
                click.echo(f"{key}: {json.dumps(value, indent=2)}")
            else:
                click.echo(f"{key}: {value}")
        click.echo("="*50)
    else:
        click.echo(f" Error: {result.get('error', 'Product not found')}")

@cli.command()
@click.argument('query')
def search(query):
    
    cli_obj = InventoryCLI()
    result = cli_obj.make_request('GET', f'/inventory/search?q={query}')
    
    if result.get('success'):
        if result['count'] == 0:
            click.echo(f"No items found matching '{query}'")
        else:
            click.echo(f"\nFound {result['count']} items matching '{query}':")
            for item in result['data']:
                click.echo(f"  [{item['id']}] {item['name']} - {item['brand']} (Stock: {item['stock_quantity']})")
    else:
        click.echo(f"Error: {result.get('error', 'Search failed')}")

if __name__ == '__main__':
    cli()