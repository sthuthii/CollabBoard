from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import timedelta
import os

# --- 1. Initialize Flask App ---
app = Flask(__name__)

# --- 2. Configuration ---
# Database Configuration (using SQLite for development)
# Get the base directory of the project
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'collabboard.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Suppresses a warning

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secret-jwt-key-for-dev') # Change in production!
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1) # Tokens expire after 1 hour

# CORS Configuration
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app, resources={r"/api/*": {"origins": "*"}}) # Allow all origins for /api routes during development

# --- 3. Initialize Extensions ---
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
bcrypt = Bcrypt(app) # For password hashing

# --- 4. Define Database Models (Placeholder for now) ---
# We will define our User, Board, Task, etc., models here in the next step.
# For now, let's just have a simple example or leave it empty.
# Example (will be replaced later with our actual models):
class ExampleModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '<ExampleModel %r>' % self.name


# --- 5. Basic Routes (for testing) ---
@app.route('/')
def home():
    return "Welcome to CollabBoard Backend!"

@app.route('/api/test_db')
def test_db():
    try:
        # Try to create a dummy entry and delete it to test DB connection
        new_entry = ExampleModel(name="test_entry")
        db.session.add(new_entry)
        db.session.commit()
        db.session.delete(new_entry)
        db.session.commit()
        return jsonify({"message": "Database connection successful!"}), 200
    except Exception as e:
        return jsonify({"message": f"Database connection failed: {str(e)}"}), 500

# --- 6. Run the App ---
if __name__ == '__main__':
    app.run(debug=True) # debug=True enables auto-reloading and better error messagest