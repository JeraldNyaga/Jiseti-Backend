from .baseModel import db, bcrypt
from datetime import datetime, timezone
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import validates
import re
class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=True, unique=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
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

