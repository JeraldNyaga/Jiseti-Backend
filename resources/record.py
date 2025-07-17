from flask import request
from flask_restful import Resource
from models import db, Record

class RecordList(Resource):
    def get(self):
        records = Record.query.all()
        return [record.to_dict() for record in records], 200

    def post(self):
        data = request.get_json()
        try:
            new_record = Record(
                title=data["title"],
                description=data["description"],
                category=data['category'],
                status=data.get("status", "under investigation")
            )
            db.session.add(new_record)
            db.session.commit()
            return new_record.to_dict(), 201
        except Exception as e:
            return {"error": str(e)}, 400


class SingleRecord(Resource):
    def get(self, record_id):
        record = Record.query.get(record_id)
        if not record:
            return {"error": "Record not found"}, 404
        return record.to_dict(), 200
