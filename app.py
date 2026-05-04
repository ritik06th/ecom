from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import event, Index
from functools import wraps
from collections import OrderedDict
import hashlib
import time
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_change_in_production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Query Log Model for Analyzer
class QueryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.Text, nullable=False)
    execution_time = db.Column(db.Float, nullable=False)
    rows_affected = db.Column(db.Integer, default=0)
    cache_hit = db.Column(db.Boolean, default=False)
    cpu_cycles = db.Column(db.Integer, default=0)
    memory_usage = db.Column(db.Integer, default=0)  # bytes approx
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_slow = db.Column(db.Boolean, default=False)  # > 0.1s

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    stock = db.Column(db.Integer, default=0)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    user = db.relationship('User', backref='cart_items')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='orders')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order = db.relationship('Order', backref='items')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# LRU Cache Simulation (max 100)
class LRUCache:
    def __init__(self, capacity=100):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = value

query_cache = LRUCache()

# Query Analyzer Decorator
def query_analyzer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        cache_key = None
        cache_hit = False

        # Simulate cache check (hash args/kwargs)
        cache_key = hashlib.md5(str(args) + str(kwargs)).hexdigest()
        cached = query_cache.get(cache_key)
        if cached:
            cache_hit = True
            return cached

        result = f(*args, **kwargs)
        exec_time = time.time() - start_time

        # Log query (simulate)
        rows = 10  # Simulate
        cpu_cycles = int(rows * 1000 * (1 if cache_hit else 2))  # Simple sim
        mem_usage = len(str(result)) if result else 1024  # Approx

        log = QueryLog(
            query=f.__name__,
            execution_time=round(exec_time, 4),
            rows_affected=rows,
            cache_hit=cache_hit,
            cpu_cycles=cpu_cycles,
            memory_usage=mem_usage,
            is_slow=exec_time > 0.1
        )
        db.session.add(log)
        db.session.commit()

        # Cache result
        if not cache_hit:
            query_cache.put(cache_key, result)

        return result
    return decorated_function

# Indexes Flag for Demo
category_indexed = False

@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registered successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/products', methods=['GET', 'POST'])
@login_required
def products():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        category = request.form['category']
        stock = int(request.form['stock'])
        product = Product(name=name, price=price, category=category, stock=stock)
        db.session.add(product)
        db.session.commit()
        flash('Product added!')
    products = Product.query.all()
    return render_template('products.html', products=products)

@app.route('/delete_product/<int:id>')
@login_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted!')
    return redirect(url_for('products'))

@app.route('/cart/add/<int:product_id>')
@login_required
def add_to_cart(product_id):
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product_id)
        db.session.add(cart_item)
    db.session.commit()
    flash('Added to cart!')
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in items)
    return render_template('cart.html', items=items, total=total)

@app.route('/cart/remove/<int:id>')
@login_required
def remove_from_cart(id):
    item = Cart.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/orders', methods=['POST'])
@login_required
@query_analyzer
def place_order():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Cart empty!')
        return redirect(url_for('cart'))
    total = sum(item.product.price * item.quantity for item in items)
    order = Order(user_id=current_user.id, total_price=total)
    db.session.add(order)
    db.session.flush()  # Get order.id
    for item in items:
        order_item = OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity)
        db.session.add(order_item)
        product = Product.query.get(item.product_id)
        product.stock -= item.quantity
    db.session.query(Cart).filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash('Order placed!')
    return redirect(url_for('orders_list'))

@app.route('/orders_list')
@login_required
def orders_list():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/dashboard')
@login_required
def dashboard():
    # Stats
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    revenue = db.session.query(db.func.sum(Order.total_price)).scalar() or 0

    # Query logs (recent 50)
    logs = QueryLog.query.order_by(QueryLog.timestamp.desc()).limit(50).all()

    # Indexing toggle demo
    global category_indexed
    return render_template('dashboard.html', 
                         total_users=total_users, total_products=total_products,
                         total_orders=total_orders, revenue=revenue, logs=logs,
                         category_indexed=category_indexed)

@app.route('/toggle_index')
@login_required
def toggle_index():
    global category_indexed
    # Simulate toggle (in real MySQL: db.engine.execute)
    category_indexed = not category_indexed
    flash(f'Category index {"added" if category_indexed else "removed"}!')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Sample data if empty
        if Product.query.count() == 0:
            products = [
                Product(name='Laptop', price=999.99, category='Electronics', stock=10),
                Product(name='T-Shirt', price=19.99, category='Clothing', stock=50),
                Product(name='Book', price=15.99, category='Books', stock=20)
            ]
            for p in products:
                db.session.add(p)
            if User.query.count() == 0:
                admin = User(name='Admin', email='admin@test.com', password=generate_password_hash('admin'), is_admin=True)
                db.session.add(admin)
            db.session.commit()
    app.run(debug=True)

