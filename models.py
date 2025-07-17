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
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    created_at= db.Column(db.DateTime, default=datetime.now)
    password_hash = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum("admin","user", name="role_enum"), nullable=False, server_default="user")

    # serialize rules
    serialize_rules = ('-password_hash', '-records.user', '-notifications.user')

    # relationships
    records = db.relationship('Record', back_populates='user', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', back_populates='user', cascade="all, delete-orphan")

    @validates ('username')
    def validate_username (self, key, username):
        if not username or len(username.strip())  < 8:
            raise ValueError ("Username must be atleast 8 characters")
        if " " in username:
            raise ValueError ("Username cannot contain spaces")
        return username.strip()
    
    @validates ('email')
    def validate_email (self, key, address):
        normalized = address.strip().lower()
        regex_validator = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
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
    category = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.now)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now)
    status = db.Column(db.Enum("under investigation", "resolved", "rejected", name="status_enum"), nullable=False, default="under investigation")
    priority = db.Column(db.Enum("medium", "high", "urgent", name="priority_enum"), nullable=False, default="medium")

    # Foreignkey
    user_id =db.Column (db.Integer, db.ForeignKey('users.id'), nullable=False)

     # Serialize rules to prevent circular references
    serialize_rules = ('-user.records', '-notifications.record')

    # relationships
    user = db.relationship ('User', back_populates = 'records')
    notifications = db.relationship('Notification', back_populates='record', cascade="all, delete-orphan")

    def __init__(self, title, description, category, status='under investigation', user_id=None):
     self.title = title
     self.description = description
     self.category = category
     self.status = status
     self.user_id = user_id


    @validates('description')
    def validate_description(self, key, description):
        if not description or len(description.strip()) < 10:
            raise ValueError("Description must be at least 10 characters long")
        return description.strip()



class Notification (db.Model, SerializerMixin):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    approved_at = db.Column(db.DateTime(), default=datetime.now)
    resolved_at = db.Column(db.DateTime(), nullable=True)
    
    # Serialize rules 
    serialize_rules = ('-user.notifications', '-record.notifications')

    #ForeignKeys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    record_id = db.Column(db.Integer, db.ForeignKey('records.id'), nullable=True)

    #Relationships
    user = db.relationship ('User', back_populates = 'notifications')
    record = db.relationship('Record', back_populates='notifications')

    @validates('message')
    def validate_message(self, key, message):
        if not message or len(message.strip()) < 1:
            raise ValueError("Message cannot be empty")
        return message.strip()
    
#the record model still has errors to be worked on tomorrow
    


