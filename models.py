from settings import db

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(100), unique=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(1000))
    status = db.Column(db.Boolean)
    owner_id = db.Column(db.Integer, db.ForeignKey('owner.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'public_id': self.public_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'owner_id': self.owner_id,
        }
    def __str__(self):
        return str(self.to_dict())

class Owner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    password = db.Column(db.String(300))
    admin = db.Column(db.Boolean)
    
    def to_dict(self):
        return {
            'id': self.id,
            'public_id': self.public_id,
            'username': self.username,
            'name': self.name,
            'admin': self.admin,
        }
    def __str__(self):
        return str(self.to_dict())