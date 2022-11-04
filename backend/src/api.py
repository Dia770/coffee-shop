# POSTMAN LINK IN CASE THE FILE IN THE PROJECT DOESNT WORK
# https://www.getpostman.com/collections/8e23ccbe0d25465528e8

from logging import exception
import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
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
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
OK '''
@app.route('/drinks', methods=['GET'])
def get_drinks():
    drinks = Drink.query.all()
    return jsonify({
        'success' : True,
        'drinks': [drink.short() for drink in drinks]
    })


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
OK '''
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    drinks = Drink.query.all()
    return jsonify({
        'success' : True,
        'drinks': [drink.long() for drink in drinks]
    })


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
OK '''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def post_drinks(jwt):
    drink_data = request.get_json()

    drink_title = drink_data['title']

    # i noticed that recipe should be a LIST of ingredient, so this is the conversion process
    drink_recipe = []
    if not isinstance(drink_data['recipe'], list):
        drink_recipe.append(drink_data['recipe'])
    else :
        drink_recipe = drink_data['recipe']

    drink_recipe_well_formated = True
    for i in drink_recipe:
        if not i.keys() >= {"color", "name", 'parts'}: # checking if each element in ingredients list has these keys
            drink_recipe_well_formated = False # False when we do not have the proper keys


    # checking if drink-title and drink-recipe exist and each element in drink-recipe has a good format
    if drink_title and drink_recipe and drink_recipe_well_formated:
        try :
            new_drink = Drink(title=drink_title, recipe=json.dumps(drink_recipe))
            new_drink.insert()

            the_new_drink = Drink.query.order_by(Drink.id.desc()).first() # querying the last record

            return jsonify({
                'success' : True,
                'drinks': [the_new_drink.long()]
            })

        except:
            # when the syntax is correct but i dont know exactly what's wrong (database constraints ofently)
            abort(422)
    else:
        # when i think that the problem is in the request
        abort(400)


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
OK '''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drinks(jwt, id):
    drink = Drink.query.get(id)
    if drink : # if a drink with that id exists

        drink_data = request.get_json()

        try:
            if 'title' in drink_data:
                drink.title = drink_data['title']

            if 'recipe' in drink_data:

                drink_recipe_well_formated = True 

                # i noticed that recipe should be a LIST of ingredient, so this is the conversion process
                drink_recipe = []
                if not isinstance(drink_data['recipe'], list):
                    drink_recipe.append(drink_data['recipe'])
                else :
                    drink_recipe = drink_data['recipe']

                for i in drink_recipe:
                    # if ("color" and 'name' and "parts") not in i:
                    if not i.keys() >= {"color", "name", 'parts'}:
                        drink_recipe_well_formated = False

                if drink_recipe_well_formated:
                    drink.recipe = json.dumps(drink_recipe)

            drink.update() 
            return jsonify({
                'success': True,
                'drinks': [drink.long()]
            })

        except:
            abort(422)

    else:
        abort(404) # there is no drink with that id



'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
OK '''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(jwt, id):
    drink = Drink.query.get(id)
    if drink :
        try:
            drink.delete()
            return jsonify({
                'success': True,
                'delete': drink.id
            })
        except:
            abort(422)
    else:
        abort(404)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

OK '''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False, 
        "error": 422, 
        "message": "unprocessable"
        }), 422

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

'''
@TODO implement error handler for 404
    error handler should conform to general task above
OK '''
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": 404, "message": "resource not found"}), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
OK '''
@app.errorhandler(AuthError)
def AuthError_catched(err):
    error = jsonify(err.error)
    error.status_code = err.status_code
    return error