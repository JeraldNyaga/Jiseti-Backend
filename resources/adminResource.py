from flask_restful import Resource, reqparse
from flask import current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.baseModel import db
from models.userModel import User
from models.recordModel import Record
from datetime import datetime, timezone
from utils import send_email_notification, send_sms_notification

def is_admin(user_id):
    user = User.query.get(user_id)
    if (user and user.role == "admin"):
        return True
    return False

class AdminResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()

        if not is_admin(user_id):
            return {'message': 'Admin access required'}, 403

        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)

        records = Record.query.paginate(page=page, per_page=per_page, error_out=False)

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
            'latitude': record.latitude,
            'longitude': record.longitude,
            'images': record.images or [],
            'status': record.status,
            'created_at': record.created_at.isoformat() if record.created_at else None,
            'updated_at': record.updated_at.isoformat() if record.updated_at else None,
            'user_id': record.user_id
        }

    @jwt_required()
    def patch(self, record_id):
        user_id = get_jwt_identity()
        
        if not is_admin(user_id):
            return {'message': 'Admin access required'}, 403
        
        record = Record.query.get(record_id)
        if not record:
            return {'message': 'Record not found'}, 404
        
        parser = reqparse.RequestParser()
        parser.add_argument('status', required=True, help='Status is required')
        #parser.add_argument('admin_comment', required=False)
        
        args = parser.parse_args()
        
        valid_statuses = ['pending', 'under investigation', 'rejected', 'resolved']
        if args['status'] not in valid_statuses:
            return {'message': 'Invalid status'}, 400
        
        try:
            old_status = record.status
            record.status = args['status']
            
            # if args.get('admin_comment'):
            #     record.admin_comment = args['admin_comment'].strip()
            
            record.updated_at = datetime.now(timezone.utc)
            db.session.commit()
            
            self.send_notification(record, old_status, args['status'])
            
            return {
                'message': f'Status updated from {old_status} to {args["status"]}',
                'record': {
                    'id': record.id,
                    'title': record.title,
                    'status': record.status,
                    'user_id': record.user_id
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error updating status: {str(e)}'}, 500
    
    def send_notification(self, record, old_status, new_status):
        if old_status == new_status:
            return
            
        user = User.query.get(record.user_id)
        if not user or not user.email:
            return
            
        subject = f"Status Update for Record #{record.id}"
        body = f"""
        Hello {user.username},
        
        The status of your record "{record.title}" has been updated:
         - Old Status: {old_status}
         - New Status: {new_status}
        
        {getattr(record, 'admin_comment', '')}
        """
        
        try:
            send_email_notification(user.email, subject, body)
            # if user.phone:
            #     send_sms_notification(user.phone, f"Record #{record.id} status updated to {new_status}")
        except Exception as e:
            # Log error but don't fail the request
            current_app.logger.error(f"Failed to send notification: {str(e)}")

