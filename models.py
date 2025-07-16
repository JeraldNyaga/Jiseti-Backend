from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates
import re

naming_convention = {
    "ix": "ix_%(column_0_label)s",  # indexing -> for better querying
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # unique
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # ck -> CHECK -> validations CHECK age > 18;
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # foreign key
    "pk": "pk_%(table_name)s",  # primary key
}

metadata = MetaData(naming_convention=naming_convention)

# create a db instance
db = SQLAlchemy(metadata=metadata)

class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    first_name = db.Column(db.String(15), nullable=False)
    last_name = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    created_at= db.Column(db.DateTime(), default=datetime.utcnow)
    password_hash = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String, default="user")


    # relationships
    records = db.relationship('Record', back_populates='user', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', back_populates='user', cascade="all, delete-orphan")

    @validates ('username')
    def validate_username (self, key, username):
        if not username or len(username.strip())  <8:
            raise ValueError ("Username must be atleast 8 characters")
        if " " in username:
            raise ValueError ("Username cannot contain spaces")
        return username.strip()
    
    @validates ('email')
    def validate_email (self, key, address):
        normalized = address.strip().lower()
        regex_validator = r"[A-Za-z][A-Za-z0-9]*(\.[A-Za-z0-9]+)*@[A-Za-z0-9]+\.[a-z]{2,}"
        if not re.match (regex_validator, normalized):
            raise ValueError ("Invalid format")
        return normalized
    
    def set_password (self,password):
        if len(password) <8:
            raise ValueError ("Password must be at least 8 characters long")
        if not any (char.isupper() for char in password):
            raise ValueError ("Password must contain at least one uppercase letter")
        if not any (char.islower() for char in password):
            raise ValueError ("Password must contain at least one lowercase letter")
        if not any (char.isdigit() for char in password):
            raise ValueError ("Password must contain at least one digit")
        
        self.password_hash = generate_password_hash(password)

class Record (db.Model, SerializerMixin):
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key =True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(), default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)

    #Foreignkey
    user_id =db.Column (db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    #relationships
    user = db.relationship ('User', back_populates = 'records')

class Notification (db.Model, SerializerMixin):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String, nullable=False)
    approved_at = db.Column(db.DateTime(), default=datetime)
    resolved_at = db.Column(db.DateTime(), default=None, nullable=True)
    resolved_at = db.Column(db.DateTime(), default=datetime)

    #ForeignKey
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    record_id = db.Column(db.Integer, db.ForeignKey('records.id'), nullable=False)

    #Relationships
    user = db.relationship ('User', back_populates = 'notifications')
    


    


