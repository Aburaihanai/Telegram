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
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username} - {self.email}>"


# ========================
# ADMIN MODEL
# ========================
class Admin(db.Model):
    __tablename__ = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"<Admin {self.email}>"


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
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)  # Optional for 'Other' category
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Shop {self.name} - {self.category}>"
