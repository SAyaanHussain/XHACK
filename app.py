from flask import Flask, render_template, request, redirect, flash, url_for
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import re
import certifi
import pymongo
import dns.resolver

app = Flask(__name__)
app.secret_key = "xhack_secret_key"
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
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html') 


# @app.route('/sign-up', methods=["GET", "POST"])
# def sign():
#     if request.method == "POST":
#         email = request.form['email']
#         password1 = request.form['password1']
#         password2 = request.form['password2']

#         if not EMAIL_REGEX.match(email):
#             flash("Invalid email format!", "danger")
#             return redirect(url_for('sign'))

#         if not check_mx_record(email):
#             flash("Invalid email domain or unable to verify the domain!", "danger")
#             return redirect(url_for('sign'))

#         if password1 != password2:
#             flash("Passwords do not match!", "danger")
#             return redirect(url_for('sign'))

#         if not PASSWORD_REGEX.match(password1):
#             flash("Password must be at least 8 characters long with uppercase, lowercase, a number, and a special character!", "danger")
#             return redirect(url_for('sign'))

#         existing_user = users_collection.find_one({"email": email})
#         if existing_user:
#             flash("Email already registered. Try logging in.", "danger")
#             return redirect(url_for('sign'))

#         hashed_password = bcrypt.generate_password_hash(password1).decode('utf-8')
#         users_collection.insert_one({"email": email, "password": hashed_password})
#         flash("Account created successfully. Please log in!", "success")
#         return redirect(url_for('login'))

#     return render_template('sign-up.html')


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
        return redirect(url_for('login'))

    return render_template('sign-up.html')


@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True, port=8862)
