from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.recordModel import Record


class LocationResource(Resource):
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
        if record.status in ['under investigation', 'rejected', 'resolved']:
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