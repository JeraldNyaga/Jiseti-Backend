from flask import request
from flask_restful import Resource
from models.userModel import User
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token

bcrypt = Bcrypt()


class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"error": "Email & password cannot be empty"}, 400
        
        # find user by email
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):

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
