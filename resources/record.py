from flask_restful import Resource, reqparse
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import Record, db, User
from datetime import datetime
from utils import send_email_notification, send_sms_notification
from werkzeug.utils import secure_filename
import os
from app import ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH, UPLOAD_FOLDER



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class RecordResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('type', required=True, help='Type is required')
    parser.add_argument('title', required=True, help='Title is required')
    parser.add_argument('description', required=True, help='Description is required')
    parser.add_argument('location_address', required=False)
    parser.add_argument('latitude', type=float, required=False)
    parser.add_argument('longitude', type=float, required=False)

    # GET all records or specific record
    @jwt_required()
    def get(self, record_id=None):
        user_id = get_jwt_identity()
        
        if record_id:
            record = Record.query.get(record_id)
            if not record:
                return {'message': 'Record not found'}, 404
            
            if record.created_by != int(user_id) and not is_admin(user_id):
                return {'message': 'Unauthorized access'}, 403
                
            return self.format_record(record)
        else:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 10, type=int), 100)
            
            if is_admin(user_id):
                records = Record.query.paginate(page=page, per_page=per_page, error_out=False)
            else:
                records = Record.query.filter_by(created_by=user_id)\
                           .paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'records': [self.format_record(r) for r in records.items],
                'pagination': {
                    'page': page,
                    'pages': records.pages,
                    'total': records.total,
                    'has_next': records.has_next,
                    'has_prev': records.has_prev
                }
            }
    
    def format_record(self, record):
        return {
            'id': record.id,
            'type': record.type,
            'title': record.title,
            'description': record.description,
            'location_address': record.location_address,
            'latitude': record.latitude,
            'longitude': record.longitude,
            'images': record.images or [],
            'videos': record.videos or [],
            'status': record.status,
            'created_by': record.created_by,
            'created_at': record.created_at.isoformat() if record.created_at else None,
            'updated_at': record.updated_at.isoformat() if record.updated_at else None,
            'admin_comment': getattr(record, 'admin_comment', None)
        }

    # CREATE new record
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        args = self.parser.parse_args()
        
        if args['type'] not in ['Red-Flag', 'Intervention']:
            return {'message': 'Type must be Red-Flag or Intervention'}, 400
        
        if args.get('latitude'):
            if not -90 <= args['latitude'] <= 90:
                return {'message': 'Invalid latitude'}, 400
                
        if args.get('longitude'):
            if not -180 <= args['longitude'] <= 180:
                return {'message': 'Invalid longitude'}, 400
        
        try:
            record = Record(
                type=args['type'],
                title=args['title'].strip(),
                description=args['description'].strip(),
                location_address=args.get('location_address', '').strip() if args.get('location_address') else None,
                latitude=args.get('latitude'),
                longitude=args.get('longitude'),
                images=[],
                videos=[],
                status='draft',
                created_by=int(user_id),
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            return {
                'message': 'Record created successfully',
                'record': self.format_record(record)
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating record: {str(e)}'}, 500
    
    # UPDATE record
    @jwt_required()
    def put(self, record_id):
        user_id = get_jwt_identity()
        record = Record.query.get(record_id)
        
        if not record:
            return {'message': 'Record not found'}, 404
            
        if record.created_by != int(user_id):
            return {'message': 'Unauthorized to edit this record'}, 403
        
        if record.status in ['under-investigation', 'rejected', 'resolved']:
            return {'message': 'Cannot edit record with current status'}, 400
        
        args = self.parser.parse_args()
        
        try:
            if args['type'] not in ['red-flag', 'intervention']:
                return {'message': 'Invalid record type'}, 400
                
            record.type = args['type']
            record.title = args['title'].strip()
            record.description = args['description'].strip()
            
            if args.get('location'):
                record.location = args['location'].strip()
            
            if args.get('latitude'):
                if not -90 <= args['latitude'] <= 90:
                    return {'message': 'Invalid latitude'}, 400
                record.latitude = args['latitude']
                
            if args.get('longitude'):
                if not -180 <= args['longitude'] <= 180:
                    return {'message': 'Invalid longitude'}, 400
                record.longitude = args['longitude']
            
            record.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'message': 'Record updated successfully',
                'record': self.format_record(record)
            }
            
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error updating record: {str(e)}'}, 500

    # DELETE record
    @jwt_required()
    def delete(self, record_id):
        user_id = get_jwt_identity()
        record = Record.query.get(record_id)
        
        if not record:
            return {'message': 'Record not found'}, 404
            
        if record.created_by != int(user_id):
            return {'message': 'Unauthorized to delete this record'}, 403
        
        if record.status in ['under-investigation', 'rejected', 'resolved']:
            return {'message': 'Cannot delete record with current status'}, 400
        
        try:
            db.session.delete(record)
            db.session.commit()
            return {'message': 'Record deleted successfully'}
            
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error deleting record: {str(e)}'}, 500

class RecordMediaResource(Resource):
    @jwt_required()
    def post(self, record_id):
        user_id = get_jwt_identity()
        record = Record.query.get(record_id)
        
        if not record:
            return {'message': 'Record not found'}, 404
            
        if record.created_by != int(user_id):
            return {'message': 'Unauthorized to modify this record'}, 403
        
        if record.status in ['under-investigation', 'rejected', 'resolved']:
            return {'message': 'Cannot modify media for record with current status'}, 400
        
        if 'file' not in request.files:
            return {'message': 'No file uploaded'}, 400
            
        file = request.files['file']
        if file.filename == '':
            return {'message': 'No selected file'}, 400
            
        if not allowed_file(file.filename):
            return {'message': 'File type not allowed'}, 400
            
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, f"record_{record_id}", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            
            media_type = 'images' if file.filename.lower().split('.')[-1] in ['jpg', 'jpeg', 'png', 'gif'] else 'videos'
            
            current_media = getattr(record, media_type) or []
            current_media.append(filepath)
            setattr(record, media_type, current_media)
            
            record.updated_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'message': 'File uploaded successfully',
                media_type: current_media
            }
            
        except Exception as e:
            return {'message': f'Error uploading file: {str(e)}'}, 500
class RecordLocationResource(Resource):
    @jwt_required()
    def patch(self, record_id):
        user_id = get_jwt_identity()
        
        record = Record.query.get(record_id)
        if not record:
            return {'message': 'Record not found'}, 404
            
        # Check ownership
        if record.created_by != int(user_id):
            return {'message': 'You can only update location for your own records'}, 403
        
        # Check if location can be updated
        if record.status in ['under-investigation', 'rejected', 'resolved']:
            return {'message': 'Cannot update location for record that is under investigation, rejected, or resolved'}, 400
        
        parser = reqparse.RequestParser()
        parser.add_argument('latitude', type=float, required=True, help='Latitude is required')
        parser.add_argument('longitude', type=float, required=True, help='Longitude is required')
        parser.add_argument('location', required=False)
        
        args = parser.parse_args()
        
        # Validate coordinates
        if not -90 <= args['latitude'] <= 90:
            return {'message': 'Latitude must be between -90 and 90'}, 400
        if not -180 <= args['longitude'] <= 180:
            return {'message': 'Longitude must be between -180 and 180'}, 400