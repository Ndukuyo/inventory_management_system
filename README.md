# inventory_management_system

A comprehensive inventory management system with Flask REST API, CLI interface, and OpenFoodFacts API integration.

# Features

- Full CRUD operations for inventory management
- Integration with OpenFoodFacts API for product enrichment
- CLI interface for easy management
- RESTful API endpoints
- In-memory database (array-based storage)
- Comprehensive unit tests
- Error handling and validation
  
## Setup and Running instructions

1. Install dependancies:
    pipenv install -r requirements.txt

2. Running the app:
    -while in the folder inventory_mangement_system 
       python app.py
   - keep this terminal open and running 
   
3 Using the cli interface
- open a new terminal
  - To list all items in the inventory:
      python cli.py list
  - To view item details:
      python cli.py view 1   i.e (view <id>)
  - To add an item:
      python cli.py add
  - To delete item:
      python cli.py 1     i.e(delete <id>)
  - To update item:
      python cli.py 1 --price 100
  - To search from inventory:
      python cli.py search "milk"
    
