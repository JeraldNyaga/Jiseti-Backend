from .baseModel import db
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime, timezone
from sqlalchemy.orm import validates
class Notification (db.Model, SerializerMixin):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    approved_at = db.Column(db.DateTime(), default=datetime.now(timezone.utc))
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
