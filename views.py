from settings import app, db
from flask import request, jsonify, make_response, session
from models import Owner, Task
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash
from decorators import token_required
from jwt import encode, decode
from datetime import datetime, timedelta
from flask_filter.query_filter import query_with_filters




@app.route('/owner/create', methods=['POST'])
def create_owner():
    data = request.get_json()
    for attr in ('username', 'password', 'name'):
        if attr not in data:
            print(f"{attr} is required", hasattr(data, attr))
            return jsonify({"message": f"{attr} is required"}), 400
    for arg in list(data.keys()):
        if not hasattr(Owner, arg):
            del data[arg]
    if Owner.query.filter_by(username=data['username']).first():
        return jsonify({"message": f"username : {data['username']} unavailable"}), 409
    hashed_password = generate_password_hash(data['password'], method='scrypt')
    del data['password']
    owner = Owner(public_id = str(uuid4()), **data, password=hashed_password, admin=False)
    db.session.add(owner)
    db.session.commit()
    return jsonify(owner.to_dict()), 201

   
# Return all owners
@app.route('/owner/get/all', methods=['GET'])
@token_required
def get_all_owners(current_owner):
    owners = Owner.query.all()
    return [ owner.to_dict() for owner in owners]


# Return one owner based on the id
@app.route('/owner/get/<string:public_id>', methods=['GET'])
@token_required
def get_owner(current_owner, public_id):
    return (owner.to_dict() 
            if (owner:=Owner.query.filter_by(public_id=public_id).first())
        else jsonify({'message': "owner not found."}), 404)


# Edit the owner of the id
@app.route('/owner/edit/<string:public_id>', methods=['PUT'])
@token_required
def edit_owner(current_owner, public_id):
    if not (owner := Owner.query.filter_by(public_id=public_id).first()):
        return (jsonify({'message': "owner not found."}), 404)
    for arg, data in request.get_json().items():
        if arg =='password':
            data  = generate_password_hash(data, method='scrypt')
        if arg=="username" and Owner.query.filter_by(username=data).first():
            return jsonify({"message": f"username : {data} unavailable"}), 409
        if arg in ('id','public_id'):
            continue
        setattr(owner, arg, data)
    db.session.commit()
    return owner.to_dict()


# Delete the owner of the id
@app.route('/owner/delete/<string:public_id>', methods=['DELETE'])
@token_required
def delete_owner(current_owner, public_id):
    if not (owner := Owner.query.filter_by(public_id=public_id).first()):
        return (jsonify({'message': "owner not found."}), 404)
    db.session.delete(owner)
    db.session.commit()
    return "", 204


@app.route('/task/create', methods=['POST'])
@token_required
def create_task(owner):
    current_owner = get_current_owner()
    data = request.get_json()
    for attr in ('description', 'title'):
        if attr not in data:
            return jsonify({"message": f"{attr} is required"}), 400
    for arg in list(data.keys()):
        if not hasattr(Task, arg) or arg=='owner_id':
            del data[arg]
    task = Task(public_id = str(uuid4()), owner_id=current_owner.id, **data, status=False)
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201

@app.route('/task/get/<string:public_id>', methods=['GET'])
@token_required
def get_task(owner, public_id):
    return (task.to_dict() 
        if (task:=Task.query.filter_by(public_id=public_id).first())
        else jsonify({'message': "Task not found."}), 404
    )
    

@app.route('/task/get/filtered', methods=['GET'])
@token_required
def get_filtered_task(owner):
    data = request.get_json()
    filter = []
    for arg in list(data.keys()):
        if not hasattr(Task, arg) or (arg=='id'):
            del data[arg]
        else:
            filter.append({
                    'field':arg,
                    'op': 'contains' if isinstance(arg, str) and (arg!='public_id') else '=',
                    'value': data[arg]
                })
    print(filter)
    tasks = query_with_filters(Task, filter)
    return (
        [task.to_dict() for task in tasks]
        if tasks
        else (jsonify({'message': "No task found."}), 404)
    )
    

@app.route('/task/edit/<string:public_id>', methods=['PUT'])
@token_required
def edit_task(owner, public_id):
    if not (task:=Task.query.filter_by(public_id=public_id).first()):
        return jsonify({'message': "Task not found."}), 404
    current_owner = get_current_owner()
    if task.owner_id!=current_owner.id:
        return jsonify({'message': "Only owner can edit task.", "current_owner_id": current_owner.id}), 403
    data = request.get_json()
    for arg in list(data.keys()):
        if not hasattr(Task, arg) or (arg not in ('owner_id', 'id', 'public_id')):
            setattr(task, arg, data[arg])
    db.session.commit()
    return task.to_dict()


@app.route('/task/delete/<string:public_id>', methods=['DELETE'])
@token_required
def delete_task(owner, public_id):
    if not (task:=Task.query.filter_by(public_id=public_id).first()):
        return jsonify({'message': "Task not found."}), 404
    current_owner = get_current_owner()
    if task.owner_id!=current_owner.id:
        return jsonify({'message': "Only owner can edit task."}), 403
    db.session.delete(task)
    db.session.commit()
    return "", 204



@app.route('/task/get/all', methods=['GET'] )
@token_required
def get_all_tasks(owner):
    tasks = Task.query.all()
    return [ task.to_dict() for task in tasks]

def get_current_owner():
    token = request.headers['x-access-token']
    return Owner.query.filter_by(
        public_id=decode(
            token, 
            app.config['SECRET_KEY'])['public_id']
        ).first()
    
    
    
@app.route('/owner/login', methods=['POST'])
def login():
    auth = request.authorization
    for arg in ('username', "password"):
        if not hasattr(auth, arg):
            return jsonify({"message": f"{arg} required"}), 400
    if not (owner:= Owner.query.filter_by(username = auth.username).first()):
        return jsonify({"message": "Username incorrect"}), 401
    if not check_password_hash(owner.password, auth.password):
        return jsonify({"message": "Password incorrect"}), 401    
    token = encode(
        {'public_id': owner.public_id, 
        'exp': datetime.now() + timedelta(minutes=2)},
        app.config['SECRET_KEY'])
    return jsonify({'token': token.decode('UTF-8')})