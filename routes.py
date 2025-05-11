from flask import render_template, request, redirect, url_for, flash
from app import app, db
from models import Users, Agent, Prospective_renter, Address, Credit_card, Property, Price, Booking, Reward_program
from datetime import datetime

@app.route('/')
def index():
    return render_template('index.html')

# User authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        user_type = request.form.get('user_type')
        
        # Check if user already exists
        existing_user = Users.query.filter_by(Email=email).first()
        if existing_user:
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = Users(
            First_name=first_name,
            Last_name=last_name,
            Phone_number=phone,
            Email=email,
            User_type=user_type
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Create agent or renter profile
        if user_type == 'agent':
            new_agent = Agent(User_ID=new_user.User_ID)
            db.session.add(new_agent)
        else:
            new_renter = Prospective_renter(User_ID=new_user.User_ID)
            db.session.add(new_renter)
        
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Copy all the other route functions from app.py here
# ...

# Add this at the end of the file
if __name__ == '__main__':
    app.run(debug=True)