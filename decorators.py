from functools import wraps
from flask import request, jsonify
from settings import app
from models import Owner

from jwt import decode



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not (token:=request.headers.get('x-access-token')):
            return jsonify({'message': 'Token is missing'}), 401
        try:
            data = decode(token, app.config['SECRET_KEY'])
        except Exception:
            return jsonify({'message': 'Token invalid'}), 401
        current_user = Owner.query.filter_by(public_id=data['public_id']).first()
        return f(current_user, *args, **kwargs)
    return decorated