# models.py
from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(100), unique=True, nullable=False)
    referral_code = db.Column(db.String(50), unique=True)
    referred_by = db.Column(db.String(50))  # referral code of the referrer
    wallet_balance = db.Column(db.Integer, default=0)
    joined = db.Column(db.DateTime, default=datetime.datetime.utcnow)
from flask_sqlalchemy import SQLAlchemy
import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id = db.Column(db.String(50), unique=True)
    username = db.Column(db.String(50))
    referred_by = db.Column(db.String, db.ForeignKey('user.id'), nullable=True)
    referrals = db.relationship('User')
    wallet_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Withdrawal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('user.id'))
    amount = db.Column(db.Float)
    requested_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    location = db.Column(db.String(50))
    price = db.Column(db.Float)
