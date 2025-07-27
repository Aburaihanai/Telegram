from flask_sqlalchemy import SQLAlchemy
import datetime
import uuid

db = SQLAlchemy()

# ========================
# USER MODEL
# ========================
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    referral_code = db.Column(db.String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4())[:8])
    referred_by = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)
    referrals = db.relationship('User', backref=db.backref('referrer', remote_side=[id]), lazy='dynamic')

    wallet_balance = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username} - {self.email}>"

# ========================
# WITHDRAWAL MODEL
# ========================
class Withdrawal(db.Model):
    __tablename__ = 'withdrawal'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='withdrawals')

    amount = db.Column(db.Float, nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Withdrawal {self.amount} by User {self.user_id}>"

# ========================
# SHOP MODEL
# ========================
class Shop(db.Model):
    __tablename__ = 'shop'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Shop {self.name} in {self.location} for ₦{self.price}>"
