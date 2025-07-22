from flask import request, jsonify
from flask_restful import Resource
from models import db, User
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token

bcrypt = Bcrypt()

class Signup(Resource):
    def post (self):
        data = request.get_json()
        username = data.get ("username")
        email = data.get ("email")
        password = data.get ("password")
        first_name = data.get ("first_name") 
        last_name = data.get ("last_name")

        if not all([username, email, password, first_name, last_name,]):
            return {"error": "All fields are required"}, 400
        
        current_user = User.query.filter((User.username ==username) | (User.email ==email)).first()
        # check if user exists
        if current_user:
            return {"error": "User already exists"}, 400
        
        hashed_password =bcrypt.generate_password_hash(password).decode("utf-8")

        #add user
        new_user = User(username =username, email=email, password_hash=hashed_password, first_name=first_name, last_name=last_name,)
        try:
            db.session.add(new_user)
            db.session.commit()
            return {"message": "User created successfully"}, 201
        except Exception as e:
            db.session.rollback()
            return {"error": "Failed to create user", "details": str(e)}, 500