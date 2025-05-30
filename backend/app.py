from flask import Flask
from routes import bp
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.register_blueprint(bp)
    return app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", debug=True)