from flask import Flask

# Create a Flask application instance
app = Flask(__name__)

# Import the routes module to register the routes with the app
from app import routes
