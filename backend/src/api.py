import os
from select import select
from selectors import SelectSelector
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
# db_drop_and_create_all()
with app.app_context():
    db_drop_and_create_all()

# ROUTES
@app.route('/drinks', methods=['GET'])
def get_drinks():
    selection = Drink.query.all()
    return jsonify({
        'success': True,
        "drinks": [drinks.short() for drinks in selection]
    }), 200


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    selection = Drink.query.all()
    # drinks = selection.long()
    return jsonify({
        'success': True,
        "drinks": [drinks.long() for drinks in selection]
    }), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(jwt):
    body = request.get_json()

    # Validate input fields
    req_title = body.get('title')
    req_recipe = body.get('recipe')

    if not req_title or not req_recipe:
        abort(422)

    # Ensure recipe is in a list format
    if isinstance(req_recipe, dict):
        req_recipe = [req_recipe]

    try:
        # Create a new drink
        new_drink = Drink(
            title=req_title,
            recipe=json.dumps(req_recipe)  # Serialize recipe to JSON
        )

        new_drink.insert()

        # Debugging: Log the ID after insertion
        print(f"Inserted Drink ID: {new_drink.id}")  # Log the inserted drink ID

        # Fetch and return the created drink
        drink = db.session.query(Drink).filter(Drink.id == new_drink.id).one_or_none()

        if not drink:
            print(f"Drink with ID {new_drink.id} not found")  # Debugging line
            abort(404)  # In case the drink is not found

        return jsonify({
            'success': True,
            "drinks": [drink.long()]
        }), 200

    except Exception as e:
        print(f"Error occurred: {e}")  # Log the error for debugging
        abort(400)


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(jwt, id):
    body = request.get_json()

    selection = db.session.query(Drink).filter(Drink.id == id).one_or_none()

    if selection is None:
        abort(404)
    
    new_title = body.get('title')
    new_recipe = body.get('recipe')

    if(new_title, new_recipe) == None:
        abort(422)

    try:
        selection.title = new_title
        # selection.recipe = json.dumps(new_recipe)
        selection.update()

        return jsonify({
            'success': True,
            "drinks": [selection.long()]
        }), 200

    except:
        abort(422)


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    drink = db.session.query(Drink).filter(Drink.id == id).one_or_none()

    if drink is None:
        abort(404)

    try:
        drink.delete()
    except:
        abort(404)
    else:
        return jsonify({
            'success': True,
            'delete': id
        }),200

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422



@app.errorhandler(404)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404

@app.errorhandler(AuthError)
def authError(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message":error.error['description'],
    }), error.status_code


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500

@app.errorhandler(403)
def permission_error(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "You do not have proper authorization"
    }), 403
