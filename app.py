from flask import Flask, request, render_template, redirect, url_for, session, flash
from models import db, User, Withdrawal, Shop
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///market_locator.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "Saif@14051990"  # Change this in production!

db.init_app(app)

# Create all tables
with app.app_context():
    db.create_all()

# ---------------------- ROUTES ---------------------- #

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        username = request.form["username"]
        ref = request.form.get("ref")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered")
            return redirect(url_for("register"))

        referred_by = User.query.filter_by(referral_code=ref).first() if ref else None

        new_user = User(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            referred_by=referred_by.id if referred_by else None,
            wallet_balance=100.0 if referred_by else 0.0,
        )

        db.session.add(new_user)

        if referred_by:
            referred_by.wallet_balance += 100  # Reward for referral

        db.session.commit()
        session["user_id"] = new_user.id

        return redirect(url_for("dashboard"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))

        flash("Invalid email or password")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Fix: Convert AppenderQuery to list so Jinja |length works
    user.referrals = user.referrals.all()

    return render_template("dashboard.html", user=user)

@app.route("/wallet")
def wallet():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("wallet.html", user=user)

@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
            if user.wallet_balance >= amount and amount > 0:
                user.wallet_balance -= amount
                withdrawal = Withdrawal(user_id=user.id, amount=amount)
                db.session.add(withdrawal)
                db.session.commit()
                flash("Withdrawal successful")
            else:
                flash("Insufficient balance or invalid amount")
        except ValueError:
            flash("Enter a valid amount")
            
    return render_template("withdraw.html", user=user)

@app.route("/leaderboard")
def leaderboard():
    top_users = User.query.order_by(User.wallet_balance.desc()).limit(10).all()
    return render_template("leaderboard.html", users=top_users)

@app.route("/refer")
def refer():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("refer.html", user=user)

@app.route("/search")
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

@app.route("/shop/new", methods=["GET", "POST"])
def create_shop():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        location = request.form["location"]
        price = float(request.form["price"])

        shop = Shop(name=name, category=category, location=location, price=price)
        db.session.add(shop)
        db.session.commit()
        flash("Shop added successfully")
        return redirect(url_for("adverts"))
    
    return render_template("shop_form.html")

@app.route("/adverts")
def adverts():
    all_shops = Shop.query.order_by(Shop.created_at.desc()).all()
    return render_template("adverts.html", shops=all_shops)

# ---------------------- Helper ---------------------- #
def get_current_user():
    user_id = session.get("user_id")
    if user_id:
        return User.query.get(user_id)
    return None

# ---------------------- Run ---------------------- #
if __name__ == "__main__":
    app.run(debug=True)
