import bcrypt
from datetime import datetime, timezone
from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shop.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


# ─────────────────────────── Models ───────────────────────────

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    cart_items = db.relationship("CartItem", backref="user", lazy=True, cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship("Product")


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    total = db.Column(db.Float, nullable=False)
    items = db.relationship("OrderItem", backref="order", lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    product = db.relationship("Product")


SAMPLE_PRODUCTS = [
    ("Spiral Notebook (200 pages)", "Wide-ruled spiral notebook, great for notes and journaling.", 3.99, 50),
    ("Ballpoint Pens (12-pack)", "Smooth-writing blue ballpoint pens, medium tip.", 5.49, 80),
    ("Mechanical Pencil Set", "0.5mm mechanical pencils with extra lead refills included.", 7.99, 60),
    ("Highlighter Set (6 colors)", "Chisel-tip fluorescent highlighters for easy studying.", 4.29, 70),
    ("3-Ring Binder (1 inch)", "Durable clear-view binder with inside pockets.", 6.99, 40),
    ("Sticky Notes (5-pack)", "3x3 inch sticky notes in assorted colors, 100 sheets each.", 5.99, 90),
    ("Scientific Calculator", "Solar-powered scientific calculator with 240 functions.", 14.99, 25),
    ("Ruler (12 inch)", "Clear plastic ruler with both metric and imperial markings.", 1.49, 120),
    ("Scissors", "Sharp stainless steel scissors with comfort-grip handles.", 4.99, 55),
    ("Backpack", "Lightweight 30L backpack with laptop sleeve and multiple pockets.", 34.99, 20),
]

with app.app_context():
    db.create_all()
    if Product.query.count() == 0:
        for name, desc, price, stock in SAMPLE_PRODUCTS:
            db.session.add(Product(name=name, description=desc, price=price, stock=stock))
        db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ─────────────────────────── Page routes ───────────────────────────

@app.route("/")
def index():
    products = Product.query.all()
    return render_template("index.html", products=products)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already taken.", "error")
            return render_template("register.html")
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Account created! Welcome.", "success")
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return render_template("login.html")
        login_user(user)
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/cart")
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = round(sum(i.product.price * i.quantity for i in items), 2)
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = db.get_or_404(Product, product_id)
    quantity = max(1, int(request.form.get("quantity", 1)))
    if product.stock < quantity:
        flash(f"Not enough stock for {product.name}.", "error")
        return redirect(url_for("index"))
    item = CartItem.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if item:
        item.quantity += quantity
    else:
        item = CartItem(user_id=current_user.id, product_id=product.id, quantity=quantity)
        db.session.add(item)
    db.session.commit()
    flash(f"{product.name} added to cart.", "success")
    return redirect(url_for("index"))


@app.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_from_cart(item_id):
    item = db.get_or_404(CartItem, item_id)
    if item.user_id != current_user.id:
        flash("Forbidden.", "error")
        return redirect(url_for("cart"))
    db.session.delete(item)
    db.session.commit()
    flash("Item removed.", "success")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart"))
    for item in items:
        if item.product.stock < item.quantity:
            flash(f"Not enough stock for {item.product.name}.", "error")
            return redirect(url_for("cart"))
    total = round(sum(i.product.price * i.quantity for i in items), 2)
    order = Order(user_id=current_user.id, total=total)
    db.session.add(order)
    db.session.flush()
    for item in items:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_purchase=item.product.price,
        ))
        item.product.stock -= item.quantity
        db.session.delete(item)
    db.session.commit()
    flash(f"Order #{order.id} placed! Total: ${total:.2f}", "success")
    return redirect(url_for("orders"))


@app.route("/orders")
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("orders.html", orders=user_orders)


# ─────────────────────────── Admin: add product ───────────────────────────

@app.route("/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price")
        stock = request.form.get("stock", 0)
        if not name or not price:
            flash("Name and price are required.", "error")
            return render_template("add_product.html")
        product = Product(name=name, description=description, price=float(price), stock=int(stock))
        db.session.add(product)
        db.session.commit()
        flash(f'"{name}" added.', "success")
        return redirect(url_for("index"))
    return render_template("add_product.html")


if __name__ == "__main__":
    app.run(debug=True)
