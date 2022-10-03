import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

DRINKS_PER_PAGE = 10

app = Flask(__name__)
setup_db(app)
CORS(app)

def paginate_drinks(req, drinks, require_details=False):
    """ Paginate drinks """
    page = req.args.get('page', 1, type=int)
    start = (page - 1)*DRINKS_PER_PAGE
    end = start + DRINKS_PER_PAGE
    formatted_drinks = []
    if require_details:
        formatted_drinks = [drink.long() for drink in drinks]
    else:
        formatted_drinks = [drink.short() for drink in drinks]

    displayed_drinks = formatted_drinks[start:end]

    return displayed_drinks

@app.after_request
def after_request(response):
    response.headers.add(
        "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
    )
    response.headers.add(
        "Access-Control-Allow-Methods", "GET,POST,PATCH,DELETE,OPTIONS"
    )

    response.headers.add(
        "Access-Control-Allow-Credentials", "true"
    )

    return response

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
'''
@app.route('/', methods=['GET'])
@app.route('/drinks', methods=['GET'])
def get_drinks():

    drinks = Drink.query.order_by(Drink.id).all()                    
    if len(drinks) == 0:
        abort(404)
    
    displayed_drinks = paginate_drinks(request, drinks)        

    return jsonify({
        'success':True,
        'drinks': displayed_drinks        
    })

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def drinks_details(jwt):
    drinks = Drink.query.order_by(Drink.id).all()    
    if len(drinks) == 0:
        abort(404)
    
    displayed_drinks = paginate_drinks(request, drinks, True)

    return jsonify({
        'success':True,
        'drinks': displayed_drinks        
    })

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(jwt):
    
    body = request.get_json()
    
    new_title = body.get('title', None)
    new_recipe = body.get('recipe', None)    

    drink = Drink(
        title=new_title,
        recipe=json.dumps(new_recipe)
    )
    drink.insert()

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


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
'''
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, id):
    
    drink = Drink.query.get(id)    
    if drink is None:
        abort(404, 'This drink does not exists !')

    body = request.get_json()

    if body.get('title', None) is not None:
        drink.title = body.get('title', None)
    
    if body.get('recipe', None) is not None:
        drink.recipe = json.dumps(body.get('recipe', None))
    
    drink.update()

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    })


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    drink = Drink.query.get(id)    
    if drink is None:
        abort(404, 'This drink does not exists !')    
    
    drink.delete()

    return jsonify({
        'success': True,
        'delete': id
    })


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

'''
'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):    
    return (
        jsonify({"success": False, "error": 404,
                "message": str(error)}),
        404,
    )

@app.errorhandler(401)
def not_found(error):    
    return (
        jsonify({"success": False, "error": 401,
                "message": str(error)}),
        401,
    )

@app.errorhandler(400)
def bad_request(error):    
    return (
        jsonify({"success": False, "error": 400,
                "message": str(error)}),
        400,
    )

@app.errorhandler(500)
def not_found(error):
    
    isAuthError = isinstance(error, AuthError)

    return (
        jsonify({"success": False, "error": int(error.status_code) if isAuthError  else 500,
                "message": str(error.error) if isAuthError else str(error)}),
        int(error.status_code) if isAuthError else 500,
    )