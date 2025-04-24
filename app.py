from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import re
import certifi
import pymongo
import dns.resolver
from functools import wraps

app = Flask(__name__)
app.secret_key = "JGHdufgewfiuASIUDIUU9831984942hyiufguwi&&&d"
bcrypt = Bcrypt(app)

client = pymongo.MongoClient(
    "mongodb+srv://XHACKLMB:LMBNISHANTINDAYAAN72724582%5E%5E&@xhacklmb.bo7zg0h.mongodb.net/",
    tls=True,
    tlsCAFile=certifi.where()
)
db = client["xhacklmb"]
users_collection = db["users"]

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&^])[A-Za-z\d@$!#%*?&^]{8,}$"
)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def check_mx_record(email):
    domain = email.split('@')[1]
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False

@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        user = users_collection.find_one({"email": email})
        if user and bcrypt.check_password_hash(user["password"], password):
            session['email'] = email  # Store email in session
            flash("Login successful!", "success")
            return redirect(url_for('main'))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/sign-up', methods=["GET", "POST"])
def sign():
    if request.method == "POST":
        email = request.form['email']
        password1 = request.form['password1']
        password2 = request.form['password2']

        if '@' not in email:
            flash("Invalid email format!", "danger")
            return redirect(url_for('sign'))

        if password1 != password2:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('sign'))

        if not PASSWORD_REGEX.match(password1):
            flash("Password must be at least 8 characters long with uppercase, lowercase, a number, and a special character!", "danger")
            return redirect(url_for('sign'))

        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            flash("Email already registered. Try logging in.", "danger")
            return redirect(url_for('sign'))

        hashed_password = bcrypt.generate_password_hash(password1).decode('utf-8')
        users_collection.insert_one({"email": email, "password": hashed_password})
        flash("Account created successfully. Please log in!", "success")
        return redirect(url_for('p1'))

    return render_template('sign-up.html')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@login_required
@app.route('/main')
def main():
    return render_template('main.html')

@login_required
@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        flash("Please log in to access the dashboard.", "danger")
        return redirect(url_for('login'))
    return render_template("dashboard.html")

@app.route('/decribe-your-style', methods=["GET", "POST"])
def p1():
    if request.method == "POST":
        selected_styles = request.form.getlist('style')
        email = session.get('email')

        if email:
            user = users_collection.find_one({"email": email})
            if user:
                users_collection.update_one(
                    {"email": email},
                    {"$set": {"selected_styles": selected_styles}}
                )
                flash("Your style preferences have been saved!", "success")
            else:
                flash("User not found. Please log in first.", "danger")
        else:
            flash("No email found in session. Please log in again.", "danger")

        return redirect(url_for('login'))

    return render_template("p1.html")


import base64
from bson.binary import Binary

closets_collection = db["closets"]

@app.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    if 'image' not in request.files:
        flash("No image uploaded.", "danger")
        return redirect(url_for('closet'))

    image_file = request.files['image']
    if image_file.filename == '':
        flash("No selected file.", "danger")
        return redirect(url_for('closet'))

    email = session.get('email')
    image_data = Binary(image_file.read())  

    closets_collection.insert_one({
        'email': email,
        'image': image_data
    })

    flash("Image uploaded successfully!", "success")
    return redirect(url_for('closet'))


@login_required
@app.route('/my-closet')
def closet():
    email = session.get('email')
    user_images = closets_collection.find({'email': email})

    images_base64 = []
    for entry in user_images:
        base64_img = base64.b64encode(entry['image']).decode('utf-8')
        images_base64.append(base64_img)

    return render_template("closet.html", images=images_base64)



@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True, port=8862)
