from .baseModel import db
from datetime import datetime, timezone
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import validates

class Record (db.Model, SerializerMixin):
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key =True)
    type = db.Column(db.Enum("Red-Flag", "Intervention", name="type_enum"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(timezone.utc))
    status = db.Column(db.Enum('pending','under investigation' ,'rejected', 'resolved', name="status_enum"), nullable=False, default="pending")
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    images = db.Column(db.JSON)  
    #videos = db.Column(db.JSON)

    # Foreignkey
    user_id =db.Column (db.Integer, db.ForeignKey('users.id'), nullable=False)

     # Serialize rules to prevent circular references
    serialize_rules = ('-user.records', '-notifications.record')

    # relationships
    user = db.relationship ('User', back_populates = 'records')
    notifications = db.relationship('Notification', back_populates='record', cascade="all, delete-orphan")

    def __init__(self, title, description, type, latitude, longitude, images=None, status='pending',user_id=None, created_at=None, updated_at=None):
        self.title = title
        self.description = description
        self.type = type
        self.status = status
        self.user_id = user_id
        self.latitude = latitude
        self.longitude = longitude
        #self.location_address = location_address
        self.images = images
        #  self.videos = videos
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

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
            "Corruption",
            "Theft", 
            "Land-grabbing",
            "Mismanagement of resources",
            "Bribery",
            "Embezzlement",
            "Fraud",
            "Other"
        ]
        
        intervention_categories = [
            "Repair bad road sections",
            "Collapsed bridges", 
            "Flooding",
            "Sewage",
            "Water shortage",
            "Electricity issues",
            "Healthcare facilities",
            "Education facilities",
            "Waste management",
            "Other"
        ]
        
        if record_type == "Red-Flag":
            return red_flag_categories
        elif record_type == "Intervention":
            return intervention_categories
        else:
            return []
        
