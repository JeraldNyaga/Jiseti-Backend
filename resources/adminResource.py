from flask_restful import Resource, reqparse
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import Record, db, User
from datetime import datetime
from utils import send_email_notification, send_sms_notification
from werkzeug.utils import secure_filename
import os
from app import ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH, UPLOAD_FOLDER

def is_admin(user_id):
    user = User.query.get(user_id)
    return user and user.is_admin

class AdminRecordResource(Resource):
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
        parser.add_argument('admin_comment', required=False)
        
        args = parser.parse_args()
        
        valid_statuses = ['draft', 'under-investigation', 'rejected', 'resolved']
        if args['status'] not in valid_statuses:
            return {'message': 'Invalid status'}, 400
        
        try:
            old_status = record.status
            record.status = args['status']
            
            if args.get('admin_comment'):
                record.admin_comment = args['admin_comment'].strip()
            
            record.updated_at = datetime.utcnow()
            db.session.commit()
            
            self.send_notification(record, old_status, args['status'])
            
            return {
                'message': f'Status updated from {old_status} to {args["status"]}',
                'record': {
                    'id': record.id,
                    'title': record.title,
                    'status': record.status,
                    'created_by': record.created_by
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error updating status: {str(e)}'}, 500
    
    def send_notification(self, record, old_status, new_status):
        if old_status == new_status:
            return
            
        user = User.query.get(record.created_by)
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
            if user.phone:
                send_sms_notification(user.phone, f"Record #{record.id} status updated to {new_status}")
        except Exception as e:
            # Log error but don't fail the request
            current_app.logger.error(f"Failed to send notification: {str(e)}")

