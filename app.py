import cloudinary
from flask import Flask
from datetime import timedelta
from flask_migrate import Migrate
from flask_restful import Api
from models.baseModel import db
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os



from resources.loginResource import LoginResource
from resources.signupResource import SignupResource
from resources.recordResource import RecordResource
from resources.adminResource import AdminResource


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

#Configure cloudinary to handle images:
cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key = os.getenv('CLOUDINARY_API_KEY'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET') 
)

#Initialize database and migrations
db.init_app(app)
migrate = Migrate(app, db)
with app.app_context():
    db.create_all()

#Initialize extensions
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

#setup cors
CORS(app, resources={r"/*": {"origins": "*"}})  

# Auth routes
api.add_resource(SignupResource, "/signup")
api.add_resource(LoginResource, "/login")

# User routes
api.add_resource(RecordResource, "/records", "/records/<int:record_id>") 


# Admin routes
api.add_resource(AdminResource, "/admin/records", "/admin/records/<int:record_id>")

#Run the Flask development server
if __name__ == '__main__':
    app.run(port=5555, debug=True)