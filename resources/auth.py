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

class Login(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"error": "Email & password cannot be empty"}, 400
        
        # find user by email
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):

            # generate access token
            access_token = create_access_token(identity=str(user.id))
            return {
                "access_token": access_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            }, 200
        else:
            return {"error": "Invalid Credentials"}, 401
