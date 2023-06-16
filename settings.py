from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from flask_migrate import Migrate






PATH_DB = 'sqlite:///'+ str(Path('sqlite.db').resolve())

app = Flask(__name__)
app.config['SECRET_KEY'] = "CoRmT7gepN1WkdxwvuxOIFRPhkE"
app.config['SQLALCHEMY_DATABASE_URI'] = PATH_DB
db = SQLAlchemy(app)
with app.app_context():
    db.create_all()
Migrate(app, db)