from flask import request
from flask_restful import Resource
from models.baseModel import db
from models.userModel import User
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

class SignupResource(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        role = data.get("role")

        if not all([username, email, password, first_name, last_name]):
            return {"error": "All fields are required"}, 400

        # Check if user already exists
        current_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if current_user:
            return {"error": "User already exists"}, 400

        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role
        )

        try:
            new_user.set_password(password) 
            db.session.add(new_user)
            db.session.commit()
            return {"message": "User created successfully"}, 201
        except ValueError as ve:
            return {"error": str(ve)}, 400
        except Exception as e:
            db.session.rollback()
            return {"error": "Failed to create user", "details": str(e)}, 500
