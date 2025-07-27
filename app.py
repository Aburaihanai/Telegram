from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from models import db, User, Shop, Withdrawal, Admin  # Ensure Admin model exists
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
import uuid

# ------------------ App Setup ------------------ #
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///market_locator.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "Saif@14051990"

# Mail Configuration
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='your_email@gmail.com',       # Replace
    MAIL_PASSWORD='your_app_password',          # Replace
)
mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

db.init_app(app)
with app.app_context():
    db.create_all()

# ------------------ Helper ------------------ #
def get_current_user():
    user_id = session.get("user_id")
    if user_id:
        return User.query.get(user_id)
    return None

# ------------------ Routes ------------------ #

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        ref = request.form.get("ref")

        if User.query.filter_by(email=email).first():
            flash("Email already exists.")
            return redirect(url_for("register"))

        # Send confirmation email
        token = s.dumps(email, salt='email-confirm')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        msg = Message("Confirm Your Email", recipients=[email])
        msg.body = f"Hi {username}, please click to confirm your email: {confirm_url}"
        mail.send(msg)
        flash("Confirmation email sent. Please check your inbox.")

        referred_by = User.query.filter_by(referral_code=ref).first() if ref else None
        new_user = User(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            referred_by=referred_by.id if referred_by else None,
            wallet_balance=100.0 if referred_by else 0.0,
            is_verified=False  # Make sure User model has this field
        )

        db.session.add(new_user)
        if referred_by:
            referred_by.wallet_balance += 100
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/confirm/<token>")
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except:
        return "Link expired or invalid."

    user = User.query.filter_by(email=email).first_or_404()
    user.is_verified = True
    db.session.commit()
    flash("Email confirmed. You can now login.")
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            if not user.is_verified:
                flash("Please verify your email first.")
                return redirect(url_for("logout"))

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

    referral_list = list(user.referrals)
    shop_count = Shop.query.count()
    total_referrals = len(referral_list)
    recent_withdrawals = Withdrawal.query.order_by(Withdrawal.requested_at.desc()).limit(5).all()

    return render_template("dashboard.html",
        user=user,
        referral_list=referral_list,
        total_referrals=total_referrals,
        shop_count=shop_count,
        recent_withdrawals=recent_withdrawals
    )

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password_hash, password):
            session["admin_id"] = admin.id
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials")
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_id"):
        return redirect(url_for("admin_login"))

    users = User.query.all()
    shops = Shop.query.all()
    withdrawals = Withdrawal.query.all()

    return render_template("admin_dashboard.html", users=users, shops=shops, withdrawals=withdrawals)

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
        amount = float(request.form.get("amount", 0))
        if user.wallet_balance >= amount:
            user.wallet_balance -= amount
            withdrawal = Withdrawal(user_id=user.id, amount=amount)
            db.session.add(withdrawal)
            db.session.commit()
            flash("Withdrawal successful")
        else:
            flash("Insufficient balance")
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

@app.route("/register_shop", methods=["GET", "POST"])
def register_shop():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    category_price_map = {
        "Clothing": 1500,
        "Groceries": 1000,
        "Electronics": 2500,
        "Furniture": 3000,
        "Supermarkets": 2000,
        "Pharmacies": 1800,
        "Other": 0
    }

    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        location = request.form["location"]

        if category == "Other":
            category = request.form.get("custom_category")
            description = request.form.get("custom_description")
            price = float(request.form.get("custom_price"))
        else:
            description = None
            price = category_price_map.get(category, 0)

        new_shop = Shop(
            name=name,
            category=category,
            location=location,
            price=price,
            description=description
        )
        db.session.add(new_shop)
        db.session.commit()
        flash("Shop registered successfully.")
        return redirect(url_for("adverts"))

    return render_template("shop_form.html", category_price_map=category_price_map)

@app.route("/adverts")
def adverts():
    all_shops = Shop.query.order_by(Shop.created_at.desc()).all()
    return render_template("adverts.html", shops=all_shops)

# ------------- Run App ------------- #
if __name__ == "__main__":
    app.run(debug=True)
