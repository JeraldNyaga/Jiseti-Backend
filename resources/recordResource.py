from flask_restful import Resource, reqparse
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.baseModel import db
from models.userModel import User
from models.recordModel import Record
from datetime import datetime, timezone


def is_admin(user_id):
    user = User.query.get(user_id)
    if (user and user.role == "admin"):
        return True
    return False

class RecordResource(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('type', required=True, help='Type is required')
    parser.add_argument('title', required=True, help='Title is required')
    parser.add_argument('description', required=True, help='Description is required')
    parser.add_argument('latitude', type=float, required=True)
    parser.add_argument('longitude', type=float, required=True)
    parser.add_argument('status', type=str, required=True)
    parser.add_argument('images', type=list, location='json', required=True)

    # GET all records or specific record
    @jwt_required()
    def get(self, record_id=None):
        user_id = get_jwt_identity()
        
        if record_id:
            record = Record.query.get(record_id)
            if not record:
                return {'message': 'Record not found'}, 404
            
            if record.user_id != int(user_id) and not is_admin(user_id):
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
            # 'location_address': record.location_address,
            'latitude': record.latitude,
            'longitude': record.longitude,
            'images': record.images or [],
            # 'videos': record.videos or [],
            'status': record.status,
            # 'created_by': record.created_by,
            'created_at': record.created_at.isoformat() if record.created_at else None,
            'updated_at': record.updated_at.isoformat() if record.updated_at else None,
            'user_id': record.user_id
            # 'admin_comment': getattr(record, 'admin_comment', None)
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
                latitude=args.get('latitude'),
                longitude=args.get('longitude'),
                images=args.get('images'),
                # videos=[],
                status='pending',
                user_id=int(user_id),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
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


