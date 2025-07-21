from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

# Telegram Web App endpoint
@app.route('/webapp')
def webapp():
    return render_template("webapp.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
# app.py
from flask import Flask, request, render_template, redirect
from models import db, User
import random
import string

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///referral.db'
db.init_app(app)

def generate_referral_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

@app.route('/start')
def start():
    telegram_id = request.args.get('telegram_id')
    referred_by = request.args.get('ref')

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        ref_code = generate_referral_code()
        user = User(telegram_id=telegram_id, referral_code=ref_code, referred_by=referred_by)
        db.session.add(user)

        # Reward referrer ₦100
        if referred_by:
            referrer = User.query.filter_by(referral_code=referred_by).first()
            if referrer:
                referrer.wallet_balance += 100
        db.session.commit()

    return f"Welcome, your referral code is: {user.referral_code}"
@app.route('/search')
def search():
    query = request.args.get('query')
    results = ShopItem.query.filter(ShopItem.name.contains(query)).all()
    return render_template("search_results.html", results=results, query=query)
from flask import Flask, request, render_template, redirect, url_for
from models import db, User, Withdrawal
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market_locator.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/register')
def register():
    telegram_id = request.args.get('telegram_id')
    username = request.args.get('username')
    ref = request.args.get('ref')  # Referral code is a user.id
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        referred_by = User.query.get(ref) if ref else None
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            referred_by=referred_by.id if referred_by else None,
            wallet_balance=100.0 if referred_by else 0.0  # reward referrer ₦100
        )
        db.session.add(new_user)
        if referred_by:
            referred_by.wallet_balance += 100
        db.session.commit()
    return redirect(url_for('dashboard', telegram_id=telegram_id))

@app.route('/dashboard')
def dashboard():
    telegram_id = request.args.get('telegram_id')
    user = User.query.filter_by(telegram_id=telegram_id).first()
    return render_template('dashboard.html', user=user)

@app.route('/withdraw')
def withdraw():
    telegram_id = request.args.get('telegram_id')
    amount = float(request.args.get('amount'))
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if user and user.wallet_balance >= amount:
        user.wallet_balance -= amount
        withdrawal = Withdrawal(user_id=user.id, amount=amount)
        db.session.add(withdrawal)
        db.session.commit()
        return "Withdrawal successful"
    return "Insufficient balance"

@app.route('/leaderboard')
def leaderboard():
    top_users = User.query.order_by(User.wallet_balance.desc()).limit(10).all()
    return render_template('leaderboard.html', users=top_users)
@app.route('/')
def start():
    return render_template('start.html')
@app.route('/refer')
def refer():
    telegram_id = request.args.get('telegram_id')
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return "User not found."

    referral_link = f"http://t.me/FindShopsNaijaNaijaBot?startapp={user.id}"
    return render_template('refer.html', user=user, referral_link=referral_link)
@app.route('/search', methods=['GET'])
def search():
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    
    query = Shop.query
    if category:
        query = query.filter(Shop.category.ilike(f"%{category}%"))
    if location:
        query = query.filter(Shop.location.ilike(f"%{location}%"))

    results = query.all()
    return render_template("search.html", results=results, category=category, location=location)
from flask import Flask, request, render_template, session
import hashlib
import hmac
import time

app = Flask(__name__)
app.secret_key = "Saif@14051990"  # Replace with a secure key

# Telegram bot token
BOT_TOKEN = 8013830409:AAEHB4eF2UtNS-YCzw8EVGxt3GyJbGElNXY

def verify_telegram_auth(data):
    auth_data = dict(data)
    hash_ = auth_data.pop("hash")
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(auth_data.items())])
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    hmac_string = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac_string == hash_

@app.route("/")
def index():
    user = request.args
    if not verify_telegram_auth(user):
        return "Authentication failed", 403

    session["telegram_user"] = user
    return render_template("index.html", user=user),\
