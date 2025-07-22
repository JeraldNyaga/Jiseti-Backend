from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Record, db
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from app import ALLOWED_EXTENSIONS, UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class ImageMediaResource(Resource):
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