from flask import Flask
from datetime import timedelta
from flask_migrate import Migrate
from flask_restful import Api, Resource
from models import db
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os

from resources.auth import Signup, Login
from resources.record import RecordList
from resources.record import SingleRecord


#load environment
load_dotenv()

#Initialize Flask app
app = Flask(__name__)

api = Api(app)  

#Configure JWT
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

#Setup  and configure Database URL
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["BUNDLE_ERRORS"] = True

#Initialize database and migrations
db.init_app(app)
migrate = Migrate(app, db)

#Initialize extensions
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

#setup cors
CORS(app)

api.add_resource(Signup, "/signup")
api.add_resource(Login, "/login")
api.add_resource(RecordList, '/records')
api.add_resource(SingleRecord, '/records/<int:record_id>')

#Run the Flask development server
if __name__ == '__main__':
    app.run(port=5555, debug=True)