from flask import request
from flask_restful import Resource
from models.userModel import User
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import jsonify


bcrypt = Bcrypt()


class LoginResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return ({"error": "User not found"}), 404

        return ({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name":user.first_name,
            "last_name":user.last_name,
            "role": user.role
        }), 200
    
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
