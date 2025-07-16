from flask import Flask
from flask_migrate import Migrate
from models import db
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://rxhma-sys:rahmamoha@localhost/jiseti_db"
db.init_app(app)
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(port=5555, debug=True)