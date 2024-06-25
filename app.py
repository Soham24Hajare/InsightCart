from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from database import db
from flask_migrate import Migrate
from models import Product, CartItem
from flask_mail import Mail, Message
import json
import sqlite3
import joblib
import numpy as np
import stripe

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'

stripe.api_key = "sk_test_51NyYskSAl0YqbydO6yLFNNPVdbMxyRhbDDaNUINFgchED26mbx1PU7l7AfWtoEGSEdYpJ6hiua4aKODKnD9DVEOc00mHxCU6uZ"
YOUR_DOMAIN = "http://localhost:5000"
db.init_app(app)
migrate = Migrate(app, db)

# Load association rules
with open('association_rules.json', 'r') as file:
    association_rules = json.load(file)

# Load scaler
scaler_path = r'C:\Users\Soham Hajare\Desktop\InsightCart\models\sc.sav'
sc = joblib.load(scaler_path)

# Load model
model_path = r'C:\Users\Soham Hajare\Desktop\InsightCart\models\lr.sav'
model = joblib.load(model_path)

# Function to initialize the database
def initialize_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, email TEXT)''')
    conn.commit()
    conn.close()

# Initialize the database
initialize_database()

@app.route('/product/<int:product_id>')
def product_details(product_id):
    # Get the product details from the database
    product = Product.query.get(product_id)
    
    # Find the association rule for the current product
    associated_products = []
    for rule in association_rules:
        # Check if the product name matches any antecedent in the association rule
        if product.name in rule['antecedents']:
            for consequent in rule['consequents']:
                # Retrieve the details of the associated product from the database
                associated_product = Product.query.filter_by(name=consequent.strip()).first()
                if associated_product:
                    associated_products.append(associated_product)
    
    return render_template('product_details.html', product=product, associated_products=associated_products)

# Endpoint to handle delete request
@app.route('/delete-item', methods=['POST'])
def delete_item():
    try:
        data = request.json
        product_id = data.get('productId')

        if product_id is None:
            return jsonify({'error': 'productId not provided in JSON data'}), 400

        # Delete item from the cart
        CartItem.query.filter_by(product_id=product_id).delete()
        db.session.commit()

        return jsonify({'message': 'Item deleted successfully'}), 200
    except Exception as e:
        print("Error occurred while deleting item:", e)
        return jsonify({'error': 'Internal server error occurred'}), 500

@app.route('/delete-items', methods=['POST'])
def delete_items():
    try:
        data = request.json
        product_id = data.get('productId')

        if product_id is None:
            return jsonify({'error': 'productId not provided in JSON data'}), 400

        # Delete item from the database
        product = Product.query.get(product_id)
        if product:
            db.session.delete(product)
            db.session.commit()
            return jsonify({'message': 'Product deleted successfully'}), 200
        else:
            return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        print("Error occurred while deleting item:", e)
        return jsonify({'error': 'Internal server error occurred'}), 500
    
# Endpoint to delete a product
@app.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        product = Product.query.get(product_id)
        if product:
            db.session.delete(product)
            db.session.commit()
            return redirect(url_for('view_products'))
        else:
            return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        print("Error occurred while deleting product:", e)
        return jsonify({'error': 'Internal server error occurred'}), 500

# Endpoint to view all products
@app.route('/view-products')
def view_products():
    products = Product.query.all()
    return render_template('view_products.html', products=products)

# Endpoint to update a product
@app.route('/update-product/<int:product_id>', methods=['POST'])
def update_product(product_id):
    try:
        product = Product.query.get(product_id)
        if product:
            # Update product details
            product.name = request.form['name']
            product.price = request.form['price']
            product.image = request.form['image']
            db.session.commit()
            return redirect(url_for('view_products'))
        else:
            return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        print("Error occurred while updating product:", e)
        return jsonify({'error': 'Internal server error occurred'}), 500


@app.route('/create-checkout-session',methods=['POST'])
def create_checkout_session():
    try:

        checkout_session = stripe.checkout.Session.create(
            line_items= [
                {
                    'price': 'price_1Ozj2uSAl0YqbydOFrgfZmqi',
                    'quantity': 1
                }
            ],
            mode = "subscription",
            success_url=YOUR_DOMAIN + "/success.html",
            cancel_url=YOUR_DOMAIN + "/cancel.html"
        )

    except Exception as e:
        return str(e)
    
    return redirect(checkout_session.url,code=303)

@app.route('/checkout')
def checkout():
    if 'username' in session:
        # Retrieve cart items from the database
        cart_items = CartItem.query.all()
        
        # Calculate total bill
        total_bill = sum(cart_item.price for cart_item in cart_items)

        return render_template('checkout.html', cart_items=cart_items, total_bill=total_bill)
    else:
        return redirect(url_for('login'))



@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ? AND email = ?", (username, password, email))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = username
            session['email'] = email
            session['role'] = 'admin' if username == 'admin' else 'user'
            if username == "admin":
                return redirect(url_for('home'))
            else:
                return redirect(url_for('user_home'))
        else:
            error = "Invalid credentials. Please try again."
            return render_template('login.html', error=error)
        
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = c.fetchone()
        
        if existing_user:
            error = "Username already exists. Please choose a different one."
            return render_template('signup.html', error=error)
        else:
            c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", (username, password, email))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('email', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'username' in session and session.get('role') == 'admin':
        products = Product.query.all()
        return render_template('home.html', products=products)
    return redirect(url_for('login'))

@app.route('/user_home')
def user_home():
    if 'username' in session and session.get('role') == 'user':
        products = Product.query.all()
        return render_template('user_home.html', products=products)
    return redirect(url_for('login'))

@app.route('/cart.html')
def cart():
    cart_items = CartItem.query.all()
    return render_template('cart.html', cart_items=cart_items)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    try:
        product_id = request.form['product_id']
        product = Product.query.get(product_id)
        cart_item = CartItem(product_id=product.id, name=product.name, price=product.price, image=product.image)
        db.session.add(cart_item)
        db.session.commit()
        
        # Fetch associated products from association_rules
        associated_products_with_images = []
        for rule in association_rules:
            if product.name in rule['antecedents']:
                for consequent in rule['consequents']:
                    associated_product = Product.query.filter_by(name=consequent.strip()).first()
                    if associated_product:
                        associated_products_with_images.append({
                            "name": associated_product.name,
                            "image": associated_product.image
                        })

        # If associated products found, send email
        if associated_products_with_images:
            send_associated_products_email(product.name, associated_products_with_images)

        return redirect(url_for('cart'))
    except Exception as e:
        error_message = "An error occurred while adding the product to the cart: " + str(e)
        return render_template('error.html', error_message=error_message)

def send_associated_products_email(product_name, associated_products_with_images):
    if 'email' in session:  # Check if user is logged in and email is stored in session
        recipient_email = session['email']
        recipient_name = session['username']
        
        # Construct the HTML body of the email
        email_body = f'<html><body style="font-family: Arial, sans-serif;">'
        email_body += f'<p>Hello {recipient_name},</p>'
        email_body += f'<p>Exciting news! You have added <strong>{product_name}</strong> to your cart.</p>'
        email_body += '<p>Based on your recent purchase, we suggest checking out these associated products:</p>'
        email_body += '<ul style="list-style-type: none; padding: 0;">'
        
        # Iterate through associated products with images and add them to the email body
        for product in associated_products_with_images:
            email_body += '<li style="margin-bottom: 10px;">'
            email_body += f'<img src="{product["image"]}" alt="{product["name"]}" style="max-width: 200px; height: auto; margin-right: 10px; vertical-align: middle;">'
            email_body += f'<span style="vertical-align: middle;">{product["name"]}</span>'
            email_body += '</li>'
        
        email_body += '</ul>'
        email_body += '<p style="margin-top: 20px;">Best regards,<br>InsightCart Team.</p>'
        email_body += '</body></html>'
        
        # Create the email message with HTML content
        msg = Message(subject='Enjoy Seamless Shopping',
                      recipients=[recipient_email],
                      html=email_body)
        
        try:
            mail.send(msg)
            print("Email sent successfully.")
        except Exception as e:
            print("Error sending email:", e)

@app.route('/add_product_form')
def add_product_form():
    return render_template('add_product.html')

@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        name = request.form['name']
        price = request.form['price']
        image = request.form['image']

        if not name or not price or not image:
            raise ValueError("All fields are required")

        price = float(price)
        new_product = Product(name=name, price=price, image=image)
        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for('home'))
    except Exception as e:
        error_message = "An error occurred while adding the product: " + str(e)
        return render_template('error.html', error_message=error_message)

@app.route('/about.html')
def about():
    return render_template('about.html')

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Update with your SMTP server
app.config['MAIL_PORT'] = 587  # Update with your SMTP port
app.config['MAIL_USE_TLS'] = True  # Enable TLS
app.config['MAIL_USERNAME'] = 'insightcart24@gmail.com'  # Update with your email username
app.config['MAIL_PASSWORD'] = 'omeq aksu msfb nbpw'  # Update with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'insightcart24@gmail.com'  # Update with your default sender email address

mail = Mail(app)

@app.route('/send_email', methods=['POST'])
def send_email():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Construct the email message
        msg = Message(subject='Message from InsightCart',
                      recipients=[email],  # Send email to the inputted email address
                      body=f'Hello {name},\n\n{message}\n\nBest regards,\nInsightCart Team.')

        try:
            # Send the email
            mail.send(msg)
            return redirect(url_for('contact_success'))
        except Exception as e:
            return render_template('error.html', error_message=str(e))

@app.route('/contact_success')
def contact_success():
    return render_template('contact_success.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')

@app.route('/sales_prediction.html', methods=['POST','GET'])
def result():
    if request.method == 'POST':
        item_weight = float(request.form['item_weight'])
        item_fat_content = float(request.form['item_fat_content'])
        item_visibility = float(request.form['item_visibility'])
        item_type = float(request.form['item_type'])
        item_mrp = float(request.form['item_mrp'])
        outlet_establishment_year= 1998
        outlet_size= 1
        outlet_location_type= 0
        outlet_type= 1

        # Prepare input data for prediction
        X = np.array([[item_weight, item_fat_content, item_visibility, item_type, item_mrp,
                       outlet_establishment_year, outlet_size, outlet_location_type, outlet_type]])

        # Standardize input data
        X_std = sc.transform(X)

        # Make prediction
        Y_pred = model.predict(X_std)

        prediction_value =float(Y_pred)

        prediction_with_units = f"{prediction_value:.2f} units"

        # Pass prediction result to the HTML template
        return render_template("sales_prediction.html", prediction = prediction_with_units)
    else:
        return render_template("sales_prediction.html", prediction=None)

if __name__ == '__main__':
    app.run(debug=True)
