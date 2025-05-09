from flask import Flask
import os
from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError

def rollback_migration():
    # Create a connection to the database
    db_url = os.environ.get('DATABASE_URL', 'postgresql://admin:secretd@localhost:5432/real_estate_db')
    engine = create_engine(db_url)
    
    # Check if the columns exist and drop them if they do
    with engine.connect() as conn:
        try:
            # Try to drop the description column if it exists
            conn.execute('ALTER TABLE property DROP COLUMN IF EXISTS description')
            print("Dropped description column")
        except ProgrammingError:
            print("Description column doesn't exist, no need to drop")
        
        try:
            # Try to drop the property_purpose column if it exists
            conn.execute('ALTER TABLE property DROP COLUMN IF EXISTS property_purpose')
            print("Dropped property_purpose column")
        except ProgrammingError:
            print("Property_purpose column doesn't exist, no need to drop")
    
    print("Migration rollback completed successfully!")

if __name__ == '__main__':
    rollback_migration()
