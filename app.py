import base64
from bson.binary import Binary
import openai
from flask import Flask, render_template, request, redirect, flash, url_for, session
from functools import wraps
import re
from flask_bcrypt import Bcrypt
import certifi
import pymongo
import dns.resolver
import json  # Import the json module for debugging

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
closets_collection = db["closets"]

PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&^])[A-Za-z\d@$!#%*?&^]{8,}$"
)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
openai.api_key = "sk-fkgskC3t5W7q3Ij_4u2tnMB4DovHOzNIywN9pPN20IT3BlbkFJ_UxTUas_kbpgWw3Pm3TCbgv9FtL2cthZUXEW35bxgA"


def check_mx_record(email):
    domain = email.split('@')[1]
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({"email": email})
        if user and bcrypt.check_password_hash(user["password"], password):
            session['email'] = email
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
    filename = image_file.filename
    description = request.form.get('description', '')  # Get the description from the form
    closets_collection.insert_one({
        'email': email,
        'image': image_data,
        'filename': filename,
        'description': description
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

@app.route('/filter-outfits', methods=["POST"])
@login_required
def filter_outfits():
    try:
        data = request.get_json()
        if not data or 'filter' not in data:
            print("Error: Invalid JSON or missing 'filter' key in request")
            return {"error": "Invalid request"}, 400
        filter_value = data.get("filter")

        print(f"Received filter value: {filter_value}")

        email = session.get("email")
        if not email:
            print("Error: Unauthorized - No email in session")
            return {"error": "Unauthorized"}, 401

        user = users_collection.find_one({"email": email})
        if not user:
            print(f"Error: User not found for email: {email}")
            return {"error": "User not found"}, 404

        # Retrieve user's closet image metadata (filename and description)
        user_images_metadata = closets_collection.find({'email': email}, {'_id': 0, 'filename': 1, 'description': 1})

        image_descriptions = [f"Filename: {img.get('filename', 'unknown')}, Description: {img.get('description', 'No description')}" for img in user_images_metadata]

        print(f"Image Descriptions: {image_descriptions}")

        if filter_value in ["summer", "winter", "spring", "autumn"]:
            prompt = f"From the following clothing items (filename and description provided), identify the most relevant items for {filter_value}. Even if the selection is limited, choose at least one item if any could be considered suitable. Respond with only the filenames of the relevant items, separated by commas."
        elif filter_value == "festival":
            prompt = f"From the following clothing items (filename and description provided), identify the most relevant items for a festival. Even if the selection is limited, choose at least one item if any could be considered suitable. Respond with only the filenames of the relevant items, separated by commas."
        elif filter_value == "style":
            preferences = user.get("selected_styles", [])
            style_description = ", ".join(preferences)
            prompt = f"According to the style preferences: {style_description}, which of the following clothing items (filename and description provided) are the most relevant? Even if the selection is limited, choose at least one item if any could be considered suitable. Respond with only the filenames of the relevant items, separated by commas."
        elif filter_value == "all":
            return {"filtered_images": [base64.b64encode(item['image']).decode('utf-8') for item in closets_collection.find({'email': email})]}, 200
        else:
            print(f"Error: Invalid filter value: {filter_value}")
            return {"error": f"Invalid filter: {filter_value}"}, 400

        messages = [
            {"role": "system", "content": "You are a helpful AI assistant that can identify clothing items based on their filename and description."},
            {"role": "user", "content": prompt},
            {"role": "user", "content": f"The user's closet items: {image_descriptions}"}
        ]

        print("Sending request to OpenAI...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=800,
            temperature=0.6
        )
        suggestions_text = response['choices'][0]['message']['content'].strip()
        suggested_filenames = [s.strip() for s in suggestions_text.split(',')]
        print(f"OpenAI Response (filenames): {suggestions_text}")
        print(f"Suggested Filenames: {suggested_filenames}")

        filtered_images_base64 = []
        for item in closets_collection.find({'email': email, 'filename': {'$in': suggested_filenames}}):
            filtered_images_base64.append(base64.b64encode(item['image']).decode('utf-8'))

        print(f"Filtered Images (base64): {json.dumps(filtered_images_base64)}")

        return {"filtered_images": filtered_images_base64}, 200

    except Exception as e:
        error_message = str(e)
        print(f"Error in filter_outfits: {error_message}")
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(debug=True, port=8862)
