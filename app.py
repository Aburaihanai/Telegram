from flask import Flask, request, render_template, redirect, url_for, session
from models import db, User, Withdrawal, Shop
from sqlalchemy import func
import random
import string
import hashlib
import hmac

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market_locator.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "Saif@14051990"  # Replace in production
BOT_TOKEN = "8013830409:AAEHB4eF2UtNS-YCzw8EVGxt3GyJbGElNXY"

db.init_app(app)

with app.app_context():
    db.create_all()

# ---------------- AUTH HELPER -----------------
def verify_telegram_auth(data):
    auth_data = dict(data)
    if "hash" not in auth_data:
        return False
    hash_ = auth_data.pop("hash")
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(auth_data.items())])
    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    hmac_string = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac_string == hash_

# ---------------- ROUTES -----------------
@app.route("/")
def index():
    user = request.args.to_dict()
    if not verify_telegram_auth(user):
        return "Authentication failed", 403

    session["telegram_user"] = user
    return render_template("index.html", user=user)

@app.route("/register")
def register():
    telegram_id = request.args.get('telegram_id')
    username = request.args.get('username')
    ref = request.args.get('ref')

    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        referred_by = User.query.get(ref) if ref else None
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            referred_by=referred_by.id if referred_by else None,
            wallet_balance=100.0 if referred_by else 0.0
        )
        db.session.add(new_user)
        if referred_by:
            referred_by.wallet_balance += 100
        db.session.commit()

    return redirect(url_for('dashboard', telegram_id=telegram_id))

@app.route("/dashboard")
def dashboard():
    telegram_id = request.args.get('telegram_id')
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return redirect(url_for('index'))
    return render_template("dashboard.html", user=user)

@app.route("/withdraw")
def withdraw():
    telegram_id = request.args.get('telegram_id')
    amount = float(request.args.get('amount', 0))
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if user and user.wallet_balance >= amount:
        user.wallet_balance -= amount
        withdrawal = Withdrawal(user_id=user.id, amount=amount)
        db.session.add(withdrawal)
        db.session.commit()
        return "Withdrawal successful"
    return "Insufficient balance"

@app.route("/leaderboard")
def leaderboard():
    top_users = User.query.order_by(User.wallet_balance.desc()).limit(10).all()
    return render_template("leaderboard.html", users=top_users)

@app.route("/refer")
def refer():
    telegram_id = request.args.get('telegram_id')
    user = User.query.filter_by(telegram_id=telegram_id).first()
    if not user:
        return "User not found."
    referral_link = f"https://t.me/FindShopsNaijaNaijaBot?startapp={user.id}"
    return render_template("refer.html", user=user, referral_link=referral_link)

@app.route("/search", methods=["GET"])
def search():
    category = request.args.get("category", "")
    location = request.args.get("location", "")

    query = Shop.query
    if category:
        query = query.filter(Shop.category.ilike(f"%{category}%"))
    if location:
        query = query.filter(Shop.location.ilike(f"%{location}%"))

    results = query.all()
    return render_template("search.html", results=results, category=category, location=location)

# ---------------- REFERRAL GENERATOR -----------------
def generate_referral_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
