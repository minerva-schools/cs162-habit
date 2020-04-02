from web import db
from flask_login import UserMixin

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True) #add a way to ensure input is unique
    password = db.Column(db.String(200)) # hashed upon the creation of User object from signup
    
    def __repr__(self):
        return "<User(id={}, username={}, password={})>".format(self.id, self.username, self.password)

db.create_all()