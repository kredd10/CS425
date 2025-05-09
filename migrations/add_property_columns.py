from __init__ import db
from flask import Flask
import os

# Create a temporary Flask app for the migration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://admin:secretd@localhost:5432/real_estate_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def run_migration():
    with app.app_context():
        # Add the new columns
        db.engine.execute('ALTER TABLE property ADD COLUMN IF NOT EXISTS description TEXT')
        db.engine.execute('ALTER TABLE property ADD COLUMN IF NOT EXISTS property_purpose VARCHAR(20) DEFAULT \'rental\'')
        
        print("Migration completed successfully!")

if __name__ == '__main__':
    run_migration()