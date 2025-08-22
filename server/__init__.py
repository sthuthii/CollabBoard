from flask import Flask, jsonify
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import timedelta
import os

def create_app():
    # --- Initialize Flask App ---
    app = Flask(__name__)

    # --- Configuration ---
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'collabboard.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # In __init__.py
    app.config['JWT_SECRET_KEY'] = 'my-super-secret-key-for-now'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

    app.config['CORS_HEADERS'] = 'Content-Type'
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # --- Initialize Extensions ---
    from .models import db # Import db from models.py
    db.init_app(app)
    
    global bcrypt # Make bcrypt accessible to other files
    bcrypt = Bcrypt(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)

    # --- Register Blueprints ---
    from .routes import api_bp # Import the Blueprint from routes.py
    app.register_blueprint(api_bp)

    # --- Basic Routes (for testing) ---
    @app.route('/')
    def home():
        return "Welcome to CollabBoard Backend!"

    # This route is now redundant since we moved the logic to routes.py
    # @app.route('/api/test_db')
    # def test_db():
    #     return jsonify({"message": "Database models defined successfully, ready for migration!"}), 200

    return app

# Main entry point for the application
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)