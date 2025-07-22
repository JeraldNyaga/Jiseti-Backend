from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime
from flask_bcrypt import Bcrypt
from sqlalchemy.orm import validates
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
import re

bcrypt = Bcrypt()

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

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=True, unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    password = db.Column(db.String(300), nullable=False)
    role = db.Column(db.String(50), default="user")

    serialize_rules = ('-password', '-records.user', '-notifications.user')

    records = db.relationship('Record', back_populates='user', foreign_keys='Record.user_id')
    notifications = db.relationship('Notification', back_populates='user', cascade="all, delete-orphan")

    @validates('username')
    def validate_username(self, key, username):
        if not username or len(username.strip()) < 8:
            raise ValueError("Username must be at least 8 characters")
        if " " in username:
            raise ValueError("Username cannot contain spaces")
        return username.strip()

    @validates('email')
    def validate_email(self, key, address):
        normalized = address.strip().lower()
        regex_validator = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(regex_validator, normalized):
            raise ValueError("Invalid format")
        return normalized

    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isupper() for char in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain at least one digit")
        
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')


class Record (db.Model, SerializerMixin):
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key =True)
    type = db.Column(db.Enum("Red-Flag", "Intervention", name="type_enum"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.now)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now)
    status = db.Column(db.Enum("pending", "under investigation", "resolved", "rejected", name="status_enum"), nullable=False, default="under investigation")
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    images = db.Column(db.JSON)  
    # videos = db.Column(db.JSON)

    # Foreignkey
    user_id =db.Column (db.Integer, db.ForeignKey('users.id'), nullable=False)

     # Serialize rules to prevent circular references
    serialize_rules = ('-user.records', '-notifications.record')

    # relationships
    user = db.relationship ('User', back_populates = 'records')
    notifications = db.relationship('Notification', back_populates='record', cascade="all, delete-orphan")

    def __init__(self, title, description, type, latitude, longitude, location_address, images=None,created_at=None,status='draft',user_id=None):
     self.title = title
     self.description = description
     self.type = type
     self.status = status
     self.user_id = user_id
     self.latitude = latitude
     self.longitude = longitude
     self.location_address = location_address
     self.images = images
    #  self.videos = videos
     self.created_at = created_at

    @validates('description')
    def validate_description(self, key, description):
        if not description or len(description.strip()) < 10:
            raise ValueError("Description must be at least 10 characters long")
        return description.strip()
    
    @validates('type')
    def validate_type(self, key, type):
        valid_types = ['Red-Flag', 'Intervention']
        if type not in valid_types:
            raise ValueError(f"Type must be one of: {', '.join(valid_types)}")
        return type
    @validates('title')
    def validate_title(self, key, title):
        if not title or len(title.strip()) < 3:
            raise ValueError("Title must be at least 3 characters long")
        
        # Valid titles for each record type
        red_flag_titles = [
            "corruption",
            "theft", 
            "land-grabbing",
            "mismanagement of resources",
            "bribery",
            "embezzlement",
            "fraud",
            "other"
        ]
        
        intervention_titles = [
            "repair bad road sections",
            "collapsed bridges", 
            "flooding",
            "sewage",
            "water shortage",
            "electricity issues",
            "healthcare facilities",
            "education facilities",
            "waste management",
            "other"
        ]
        
        normalized_title = title.strip().lower()
        normalized_red_flags = [t.lower() for t in red_flag_titles]
        normalized_interventions = [t.lower() for t in intervention_titles]
        
        # Validate based on record title
        if hasattr(self, 'title') and self.title:
            if self.type == "Red-Flag" and normalized_title not in normalized_red_flags:
                raise ValueError(f"Invalid title for Red-Flag. Valid titles are: {', '.join(red_flag_titles)}")
            elif self.type == "Intervention" and normalized_title not in normalized_interventions:
                raise ValueError(f"Invalid title for Intervention. Valid titles are: {', '.join(intervention_titles)}")
        
        return normalized_title
    @validates('latitude')
    def validate_latitude(self, key, latitude):
        if latitude is not None:
            if not isinstance(latitude, (int, float)):
                raise ValueError("Latitude must be a number")
            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude must be between -90 and 90")
        return latitude
    @validates('longitude')
    def validate_longitude(self, key, longitude):
        if longitude is not None:
            if not isinstance(longitude, (int, float)):
                raise ValueError("Longitude must be a number")
            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude must be between -180 and 180")
        return longitude
    
    def get_categories_for_type(record_type):

        red_flag_categories = [
            "corruption",
            "theft", 
            "land-grabbing",
            "mismanagement of resources",
            "bribery",
            "embezzlement",
            "fraud",
            "other"
        ]
        
        intervention_categories = [
            "repair bad road sections",
            "collapsed bridges", 
            "flooding",
            "sewage",
            "water shortage",
            "electricity issues",
            "healthcare facilities",
            "education facilities",
            "waste management",
            "other"
        ]
        
        if record_type == "Red-Flag":
            return red_flag_categories
        elif record_type == "Intervention":
            return intervention_categories
        else:
            return []
        

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
    


