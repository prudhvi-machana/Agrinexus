from flask import Flask
from app.db.database import init_db
from dotenv import load_dotenv
import os

def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "your_secret_key"



    load_dotenv()  # Loads variables from .env file

    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

    # initialize database
    init_db(app)

    # import blueprints
    from app.routes.home_routes import home_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.farmer_routes import farmer_bp
    from app.routes.land_routes import land_bp
    from app.routes.crop_routes import crop_bp
    from app.routes.loan_routes import loan_bp
    from app.routes.subsidy_routes import subsidy_bp
    from app.routes.scheme_routes import scheme_bp
    from app.routes.farmer_portal_routes import farmer_portal_bp

    # register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(farmer_bp)
    app.register_blueprint(land_bp)
    app.register_blueprint(crop_bp)
    app.register_blueprint(loan_bp)
    app.register_blueprint(subsidy_bp)
    app.register_blueprint(scheme_bp)
    app.register_blueprint(farmer_portal_bp)

    return app