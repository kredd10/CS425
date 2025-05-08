from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_testing')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://admin:secret@localhost:5432/real_estate_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import db from models and initialize it with the app
from models import db
db.init_app(app)

# Import models after db initialization but before routes
from models import Users, Agent, Prospective_renter, Address, Credit_card, Property, Price, Booking, Reward_program, Neighborhood, Property_features

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
        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = Users(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone,
            email=email,
            user_type=user_type
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Create agent or renter profile
        if user_type == 'agent':
            new_agent = Agent(user_id=new_user.user_id)
            db.session.add(new_agent)
        else:
            new_renter = Prospective_renter(user_id=new_user.user_id)
            db.session.add(new_renter)
        
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = Users.query.filter_by(email=email).first()
        if not user:
            flash('Invalid credentials')
            return redirect(url_for('login'))
        
        session['user_id'] = user.user_id
        session['user_type'] = user.user_type
        
        flash(f'Welcome, {user.first_name}!')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    user = Users.query.get(session['user_id'])
    
    if user.user_type == 'agent':
        agent = Agent.query.filter_by(user_id=user.user_id).first()
        properties = Property.query.filter_by(agent_id=agent.agent_id).all()
        return render_template('agent_dashboard.html', user=user, agent=agent, properties=properties)
    else:
        renter = Prospective_renter.query.filter_by(user_id=user.user_id).first()
        bookings = Booking.query.filter_by(renter_id=renter.renter_id).all()
        return render_template('renter_dashboard.html', user=user, renter=renter, bookings=bookings)

# Property routes
@app.route('/properties')
def properties():
    # Get all properties
    properties = Property.query.all()
    
    # For each property, get the latest price
    for prop in properties:
        latest_price = Price.query.filter_by(property_id=prop.property_id).order_by(Price.effective_date.desc()).first()
        if latest_price:
            prop.current_price = latest_price.rental_price
        else:
            prop.current_price = None
    
    return render_template('properties.html', properties=properties)

@app.route('/property/<int:property_id>')
def property_detail(property_id):
    property = Property.query.get_or_404(property_id)
    address = Address.query.get(property.address_id)
    features = Property_features.query.filter_by(property_id=property_id).first()
    price = Price.query.filter_by(property_id=property_id).order_by(Price.effective_date.desc()).first()
    
    # Get neighborhood if available
    neighborhood = None
    if property.neighborhood_id:
        neighborhood = Neighborhood.query.get(property.neighborhood_id)
    
    # Get agent information
    agent = None
    agent_id = None
    if property.agent_id:
        agent_user = db.session.query(Users).join(Agent, Users.user_id == Agent.user_id).filter(Agent.agent_id == property.agent_id).first()
        if agent_user:
            agent = agent_user
            agent_id = property.agent_id
    
    return render_template('property_detail.html', 
                          property=property, 
                          address=address, 
                          features=features, 
                          price=price, 
                          neighborhood=neighborhood, 
                          agent=agent,
                          agent_id=agent_id)

@app.route('/search', methods=['GET', 'POST'])
def search_properties():
    if request.method == 'POST':
        city = request.form.get('city')
        property_type = request.form.get('type')
        min_price = request.form.get('min_price')
        max_price = request.form.get('max_price')
        
        # Base query - use Property instead of property
        query = db.session.query(Property, Price).\
            join(Price, Property.property_id == Price.property_id).\
            join(Address, Property.address_id == Address.address_id)
        
        # Apply filters
        if city:
            query = query.filter(Address.city.ilike(f'%{city}%'))
        if property_type and property_type != 'all':
            query = query.filter(Property.type == property_type)
        if min_price:
            query = query.filter(Price.rental_price >= min_price)
        if max_price:
            query = query.filter(Price.rental_price <= max_price)
        
        # Get latest price for each property
        results = []
        for prop, price in query.all():
            latest_price = Price.query.filter_by(property_id=prop.property_id).order_by(Price.effective_date.desc()).first()
            if latest_price:
                results.append((prop, latest_price))
        
        return render_template('search_results.html', results=results)
    
    return render_template('search.html')

# Booking routes
@app.route('/book/<int:property_id>', methods=['GET', 'POST'])
def book_property(property_id):
    if 'user_id' not in session or session['user_type'] != 'prospective_renter':
        flash('You must be logged in as a renter to book properties')
        return redirect(url_for('login'))
    
    property = Property.query.get_or_404(property_id)
    renter = Prospective_renter.query.filter_by(user_id=session['user_id']).first()
    
    if request.method == 'POST':
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        card_id = request.form.get('card_id')
        
        # Check if property is available
        existing_bookings = Booking.query.filter_by(property_id=property_id).all()
        for booking in existing_bookings:
            if (start_date <= booking.lease_till_date and end_date >= booking.start_date):
                flash('Property is not available for the selected dates')
                return redirect(url_for('book_property', property_id=property_id))
        
        # Create booking
        new_booking = Booking(
            property_id=property_id,
            renter_id=renter.renter_id,
            card_id=card_id,
            start_date=start_date,
            lease_till_date=end_date
        )
        db.session.add(new_booking)
        db.session.commit()
        
        # Add reward points
        current_price = Price.query.filter_by(property_id=property_id).order_by(Price.effective_date.desc()).first()
        if current_price:
            reward_points = int(current_price.rental_price)
            new_reward = Reward_program(
                renter_id=renter.renter_id,
                booking_id=new_booking.booking_id,
                reward_points=reward_points
            )
            db.session.add(new_reward)
            db.session.commit()
        
        flash('Property booked successfully!')
        return redirect(url_for('dashboard'))
    
    credit_cards = Credit_card.query.filter_by(renter_id=renter.renter_id).all()
    current_price = Price.query.filter_by(property_id=property_id).order_by(Price.effective_date.desc()).first()
    
    return render_template('book_property.html', property=property, credit_cards=credit_cards, price=current_price)

# User profile routes
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    user = Users.query.get(session['user_id'])
    addresses = Address.query.filter_by(user_id=user.user_id).all()
    
    if user.user_type == 'prospective_renter':
        renter = Prospective_renter.query.filter_by(user_id=user.user_id).first()
        credit_cards = Credit_card.query.filter_by(renter_id=renter.renter_id).all()
        return render_template('renter_profile.html', user=user, renter=renter, addresses=addresses, credit_cards=credit_cards)
    else:
        agent = Agent.query.filter_by(user_id=user.user_id).first()
        return render_template('agent_profile.html', user=user, agent=agent, addresses=addresses)

# Agent property management routes
@app.route('/add_property', methods=['GET', 'POST'])
def add_property():
    if 'user_id' not in session or session['user_type'] != 'agent':
        flash('You must be logged in as an agent to add properties')
        return redirect(url_for('login'))
    
    agent = Agent.query.filter_by(user_id=session['user_id']).first()
    
    if request.method == 'POST':
        # Get form data
        street = request.form.get('street')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')
        country = request.form.get('country')
        
        property_type = request.form.get('type')
        rooms = request.form.get('rooms')
        square_footage = request.form.get('square_footage')
        agency_name = request.form.get('agency_name')
        business_type = request.form.get('business_type')
        
        rental_price = request.form.get('rental_price')
        neighborhood_id = request.form.get('neighborhood_id')
        
        # Create address with the correct address_type
        new_address = Address(
            user_id=session['user_id'],
            street=street,
            city=city,
            state=state,
            zip_code=zip_code,
            country=country,
            address_type='property'  # Use 'property' as the address type for properties
        )
        db.session.add(new_address)
        db.session.flush()  # Get the address_id without committing
        
        # Create property
        new_property = Property(
            address_id=new_address.address_id,
            agent_id=agent.agent_id,
            neighborhood_id=neighborhood_id if neighborhood_id else None,
            type=property_type,
            number_of_rooms=rooms if rooms else None,
            square_footage=square_footage if square_footage else None,
            agency_name=agency_name,
            type_of_business=business_type,
            availability=True
        )
        db.session.add(new_property)
        db.session.flush()  # Get the property_id without committing
        
        # Create price
        new_price = Price(
            property_id=new_property.property_id,
            rental_price=rental_price
        )
        db.session.add(new_price)
        
        # Create property features
        has_vacation = request.form.get('has_vacation_home') == 'on'
        has_land = request.form.get('has_land_available') == 'on'
        has_amenities = request.form.get('amenities_available') == 'on'
        
        new_features = Property_features(
            property_id=new_property.property_id,
            has_vacation_home=has_vacation,
            has_land_available=has_land,
            amenities_available=has_amenities
        )
        db.session.add(new_features)
        
        try:
            db.session.commit()
            flash('Property added successfully!')
            return redirect(url_for('manage_properties'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding property: {str(e)}')
            return redirect(url_for('add_property'))
    
    # Get neighborhoods for dropdown
    neighborhoods = Neighborhood.query.all()
    return render_template('add_property.html', neighborhoods=neighborhoods)

@app.route('/manage_properties')
def manage_properties():
    if 'user_id' not in session or session['user_type'] != 'agent':
        flash('You must be logged in as an agent to manage properties')
        return redirect(url_for('login'))
    
    agent = Agent.query.filter_by(user_id=session['user_id']).first()
    properties = Property.query.filter_by(agent_id=agent.agent_id).all()
    
    # For each property, get the latest price
    for prop in properties:
        latest_price = Price.query.filter_by(property_id=prop.property_id).order_by(Price.effective_date.desc()).first()
        if latest_price:
            prop.current_price = latest_price.rental_price
        else:
            prop.current_price = None
    
    return render_template('manage_properties.html', properties=properties)

@app.route('/edit_property/<int:property_id>', methods=['GET', 'POST'])
def edit_property(property_id):
    if 'user_id' not in session or session['user_type'] != 'agent':
        flash('You must be logged in as an agent to edit properties')
        return redirect(url_for('login'))
    
    agent = Agent.query.filter_by(user_id=session['user_id']).first()
    property = Property.query.get_or_404(property_id)
    
    # Check if the property belongs to this agent
    if property.agent_id != agent.agent_id:
        flash('You can only edit your own properties')
        return redirect(url_for('manage_properties'))
    
    address = Address.query.get(property.address_id)
    features = Property_features.query.get(property_id)
    current_price = Price.query.filter_by(property_id=property_id).order_by(Price.effective_date.desc()).first()
    
    if request.method == 'POST':
        # Update address
        address.street = request.form.get('street')
        address.city = request.form.get('city')
        address.state = request.form.get('state')
        address.zip_code = request.form.get('zip_code')
        address.country = request.form.get('country')
        
        # Update property
        property.type = request.form.get('type')
        property.number_of_rooms = request.form.get('rooms')
        property.square_footage = request.form.get('square_footage')
        property.agency_name = request.form.get('agency_name')
        property.type_of_business = request.form.get('business_type')
        property.neighborhood_id = request.form.get('neighborhood_id')
        property.availability = request.form.get('availability') == 'on'
        
        # Update price if changed
        new_price = request.form.get('rental_price')
        if float(new_price) != float(current_price.rental_price):
            price = Price(
                property_id=property_id,
                rental_price=new_price
            )
            db.session.add(price)
        
        # Update features
        features.has_vacation_home = request.form.get('has_vacation_home') == 'on'
        features.has_land_available = request.form.get('has_land_available') == 'on'
        features.amenities_available = request.form.get('amenities_available') == 'on'
        
        db.session.commit()
        flash('Property updated successfully!')
        return redirect(url_for('manage_properties'))
    
    neighborhoods = Neighborhood.query.all()
    return render_template('edit_property.html', 
                          property=property, 
                          address=address, 
                          features=features, 
                          price=current_price, 
                          neighborhoods=neighborhoods)

@app.route('/delete_property/<int:property_id>', methods=['POST'])
def delete_property(property_id):
    if 'user_id' not in session or session['user_type'] != 'agent':
        flash('You must be logged in as an agent to delete properties')
        return redirect(url_for('login'))
    
    agent = Agent.query.filter_by(user_id=session['user_id']).first()
    property = Property.query.get_or_404(property_id)
    
    # Check if the property belongs to this agent
    if property.agent_id != agent.agent_id:
        flash('You can only delete your own properties')
        return redirect(url_for('manage_properties'))
    
    # Delete the property (cascade will handle related records)
    db.session.delete(property)
    db.session.commit()
    
    flash('Property deleted successfully!')
    return redirect(url_for('manage_properties'))

# Address management routes
@app.route('/add_address', methods=['GET', 'POST'])
def add_address():
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    warning = None
    
    if request.method == 'POST':
        street = request.form.get('street')
        city = request.form.get('city')
        state = request.form.get('state')
        zip_code = request.form.get('zip_code')
        country = request.form.get('country')
        address_type = request.form.get('address_type')
        
        # Validate address_type is one of the allowed values
        allowed_types = ['home', 'work', 'property', 'other']
        if address_type not in allowed_types:
            warning = f"Invalid address type '{address_type}'. Only {', '.join(allowed_types)} are allowed."
            return render_template('add_address.html', warning=warning)
        
        try:
            new_address = Address(
                user_id=session['user_id'],
                street=street,
                city=city,
                state=state,
                zip_code=zip_code,
                country=country,
                address_type=address_type
            )
            
            db.session.add(new_address)
            db.session.commit()
            
            flash('Address added successfully!')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            warning = f"Error adding address: {str(e)}"
            return render_template('add_address.html', warning=warning)
    
    return render_template('add_address.html', warning=warning)

@app.route('/edit_address/<int:address_id>', methods=['GET', 'POST'])
def edit_address(address_id):
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    address = Address.query.get_or_404(address_id)
    warning = None
    
    # Check if the address belongs to this user
    if address.user_id != session['user_id']:
        flash('You can only edit your own addresses')
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        address.street = request.form.get('street')
        address.city = request.form.get('city')
        address.state = request.form.get('state')
        address.zip_code = request.form.get('zip_code')
        address.country = request.form.get('country')
        
        # Validate address_type is one of the allowed values
        address_type = request.form.get('address_type')
        allowed_types = ['home', 'work', 'property', 'other']
        if address_type not in allowed_types:
            warning = f"Invalid address type '{address_type}'. Only {', '.join(allowed_types)} are allowed."
            return render_template('edit_address.html', address=address, warning=warning)
        
        address.address_type = address_type
        
        try:
            db.session.commit()
            flash('Address updated successfully!')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            warning = f"Error updating address: {str(e)}"
            return render_template('edit_address.html', address=address, warning=warning)
    
    return render_template('edit_address.html', address=address, warning=warning)

@app.route('/delete_address/<int:address_id>', methods=['POST'])
def delete_address(address_id):
    if 'user_id' not in session:
        flash('Please log in first')
        return redirect(url_for('login'))
    
    address = Address.query.get_or_404(address_id)
    
    # Check if the address belongs to this user
    if address.user_id != session['user_id']:
        flash('You can only delete your own addresses')
        return redirect(url_for('profile'))
    
    # Check if the address is used by any credit cards
    if Credit_card.query.filter_by(payment_address_id=address_id).first():
        flash('This address is used by one or more payment methods and cannot be deleted')
        return redirect(url_for('profile'))
    
    # Check if the address is used by any properties
    if Property.query.filter_by(address_id=address_id).first():
        flash('This address is used by one or more properties and cannot be deleted')
        return redirect(url_for('profile'))
    
    db.session.delete(address)
    db.session.commit()
    
    flash('Address deleted successfully!')
    return redirect(url_for('profile'))

# Credit card management routes
@app.route('/add_card', methods=['GET', 'POST'])
def add_card():
    if 'user_id' not in session or session['user_type'] != 'prospective_renter':
        flash('Only renters can add payment methods')
        return redirect(url_for('login'))
    
    renter = Prospective_renter.query.filter_by(user_id=session['user_id']).first()
    
    # Get addresses that can be used for billing (home, work, or other)
    addresses = Address.query.filter_by(user_id=session['user_id']).filter(
        Address.address_type.in_(['home', 'work', 'other'])
    ).all()
    
    if request.method == 'POST':
        card_number = request.form.get('card_number')
        expiry_month = request.form.get('expiry_month')
        expiry_year = request.form.get('expiry_year')
        payment_address_id = request.form.get('payment_address_id')
        
        # Check if card already exists
        existing_card = Credit_card.query.filter_by(card_number=card_number).first()
        if existing_card:
            flash('This card is already registered')
            return redirect(url_for('add_card'))
        
        # Create expiry date
        expiry_date = datetime(int(expiry_year), int(expiry_month), 1).date()
        
        new_card = Credit_card(
            card_number=card_number,
            renter_id=renter.renter_id,
            expiry_date=expiry_date,
            payment_address_id=payment_address_id
        )
        
        try:
            db.session.add(new_card)
            db.session.commit()
            flash('Payment method added successfully!')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding payment method: {str(e)}')
            return redirect(url_for('add_card'))
    
    # Check if user has any addresses
    if not addresses:
        flash('Please add a home or work address before adding a payment method')
        return redirect(url_for('add_address'))
    
    return render_template('add_card.html', addresses=addresses)

@app.route('/edit_card/<int:card_id>', methods=['GET', 'POST'])
def edit_card(card_id):
    if 'user_id' not in session or session['user_type'] != 'prospective_renter':
        flash('Only renters can edit payment methods')
        return redirect(url_for('login'))
    
    renter = Prospective_renter.query.filter_by(user_id=session['user_id']).first()
    card = Credit_card.query.get_or_404(card_id)
    
    # Check if the card belongs to this renter
    if card.renter_id != renter.renter_id:
        flash('You can only edit your own payment methods')
        return redirect(url_for('profile'))
    
    addresses = Address.query.filter_by(user_id=session['user_id']).all()
    
    if request.method == 'POST':
        # We don't allow changing the card number for security reasons
        expiry_month = request.form.get('expiry_month')
        expiry_year = request.form.get('expiry_year')
        payment_address_id = request.form.get('payment_address_id')
        
        # Create expiry date
        expiry_date = datetime(int(expiry_year), int(expiry_month), 1).date()
        
        card.expiry_date = expiry_date
        card.payment_address_id = payment_address_id
        
        db.session.commit()
        
        flash('Payment method updated successfully!')
        return redirect(url_for('profile'))
    
    # Extract month and year from expiry date
    expiry_month = card.expiry_date.month
    expiry_year = card.expiry_date.year
    
    return render_template('edit_card.html', card=card, addresses=addresses, expiry_month=expiry_month, expiry_year=expiry_year)

@app.route('/delete_card/<int:card_id>', methods=['POST'])
def delete_card(card_id):
    if 'user_id' not in session or session['user_type'] != 'prospective_renter':
        flash('Only renters can delete payment methods')
        return redirect(url_for('login'))
    
    renter = Prospective_renter.query.filter_by(user_id=session['user_id']).first()
    card = Credit_card.query.get_or_404(card_id)
    
    # Check if the card belongs to this renter
    if card.renter_id != renter.renter_id:
        flash('You can only delete your own payment methods')
        return redirect(url_for('profile'))
    
    # Check if the card is used by any bookings
    if Booking.query.filter_by(card_id=card_id).first():
        flash('This payment method is used by one or more bookings and cannot be deleted')
        return redirect(url_for('profile'))
    
    db.session.delete(card)
    db.session.commit()
    
    flash('Payment method deleted successfully!')
    return redirect(url_for('profile'))

@app.route('/check_address_constraint')
def check_address_constraint():
    # Query to get the constraint definition
    query = """
    SELECT pg_get_constraintdef(c.oid)
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    WHERE t.relname = 'address' AND c.conname = 'address_address_type_check'
    """
    
    result = db.session.execute(query).fetchone()
    constraint_def = result[0] if result else 'Constraint not found'
    
    # Display the constraint definition
    return f"<h3>Address Type Constraint:</h3><pre>{constraint_def}</pre>"

if __name__ == '__main__':
    app.run(debug=True)



