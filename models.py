from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Create a db instance
db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(250), nullable=False)
    last_name = db.Column(db.String(250), nullable=False)
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(250), unique=True, nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    
    addresses = db.relationship('Address', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.first_name} {self.last_name}>'

class Agent(db.Model):
    __tablename__ = 'agent'
    
    agent_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), unique=True, nullable=False)
    job_title = db.Column(db.String(250))
    agency_name = db.Column(db.String(250))
    contract_type = db.Column(db.String(50))
    contract_start_date = db.Column(db.Date)
    contract_end_date = db.Column(db.Date)
    salary = db.Column(db.Numeric(10, 2))
    commission = db.Column(db.Numeric(10, 2))
    
    properties = db.relationship('Property', backref='agent', lazy=True)
    user = db.relationship('Users', backref='agent_profile', uselist=False)
    
    def __repr__(self):
        return f'<Agent {self.agent_id}>'

class Prospective_renter(db.Model):
    __tablename__ = 'prospective_renter'
    
    renter_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), unique=True, nullable=False)
    move_in_date = db.Column(db.Date)
    preferred_location = db.Column(db.String(250))
    budget = db.Column(db.Numeric(10, 2))
    
    credit_cards = db.relationship('Credit_card', backref='renter', lazy=True)
    bookings = db.relationship('Booking', backref='renter', lazy=True)
    rewards = db.relationship('Reward_program', backref='renter', lazy=True)
    user = db.relationship('Users', backref='renter_profile', uselist=False)
    
    def __repr__(self):
        return f'<Renter {self.renter_id}>'

class Address(db.Model):
    __tablename__ = 'address'
    
    address_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    street = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(250), nullable=False)
    state = db.Column(db.String(250))
    zip_code = db.Column(db.String(10))
    country = db.Column(db.String(250))
    address_type = db.Column(db.String(10), nullable=False)
    
    # Update CheckConstraint to match SQL schema
    __table_args__ = (
        db.CheckConstraint(
            "address_type IN ('primary', 'payment')",
            name='address_address_type_check'
        ),
    )
    
    properties = db.relationship('Property', backref='address', lazy=True)
    payment_cards = db.relationship('Credit_card', backref='payment_address', lazy=True)
    
    def __repr__(self):
        return f'<Address {self.street}, {self.city}>'

class Credit_card(db.Model):
    __tablename__ = 'credit_card'
    
    card_id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(20), unique=True, nullable=False)
    renter_id = db.Column(db.Integer, db.ForeignKey('prospective_renter.renter_id', ondelete='CASCADE'), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    payment_address_id = db.Column(db.Integer, db.ForeignKey('address.address_id', ondelete='RESTRICT'), nullable=False)
    
    bookings = db.relationship('Booking', backref='credit_card', lazy=True)
    
    def __repr__(self):
        return f'<Credit Card {self.card_id}>'

class Neighborhood(db.Model):
    __tablename__ = 'neighborhood'
    
    neighborhood_id = db.Column(db.Integer, primary_key=True)
    neighborhood_name = db.Column(db.String(250), nullable=False)
    crime_rate = db.Column(db.Numeric(5, 2))
    school_rating = db.Column(db.Integer)
    has_vacation_home = db.Column(db.Boolean)
    has_land_available = db.Column(db.Boolean)
    amenities_available = db.Column(db.Boolean)
    
    properties = db.relationship('Property', backref='neighborhood', lazy=True)
    
    def __repr__(self):
        return f'<Neighborhood {self.neighborhood_name}>'

class Property(db.Model):
    __tablename__ = 'property'
    
    property_id = db.Column(db.Integer, primary_key=True)
    address_id = db.Column(db.Integer, db.ForeignKey('address.address_id', ondelete='CASCADE'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.agent_id', ondelete='RESTRICT'), nullable=False)
    neighborhood_id = db.Column(db.Integer, db.ForeignKey('neighborhood.neighborhood_id', ondelete='SET NULL'))
    type = db.Column(db.String(20), nullable=False)
    number_of_rooms = db.Column(db.Integer)
    square_footage = db.Column(db.Numeric(10, 2))
    agency_name = db.Column(db.String(250))
    type_of_business = db.Column(db.String(250))
    availability = db.Column(db.Boolean, nullable=False)
    # Remove the description and property_purpose columns
    
    prices = db.relationship('Price', backref='property', lazy=True, cascade="all, delete-orphan", passive_deletes=True)
    bookings = db.relationship('Booking', backref='property', lazy=True, cascade="all, delete-orphan", passive_deletes=True)
    features = db.relationship('Property_features', backref='property', uselist=False, lazy=True, cascade="all, delete-orphan", passive_deletes=True)
    
    def __repr__(self):
        return f'<Property {self.property_id}>'

class Property_features(db.Model):
    __tablename__ = 'property_features'
    
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id', ondelete='CASCADE'), primary_key=True)
    has_vacation_home = db.Column(db.Boolean, default=False)
    has_land_available = db.Column(db.Boolean, default=False)
    amenities_available = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Property Features {self.property_id}>'

class Price(db.Model):
    __tablename__ = 'price'
    
    price_id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id', ondelete='CASCADE'), nullable=False)
    rental_price = db.Column(db.Numeric(10, 2), nullable=False)
    effective_date = db.Column(db.Date, default=datetime.utcnow().date())
    
    def __repr__(self):
        return f'<Price {self.price_id}>'

class Booking(db.Model):
    __tablename__ = 'booking'
    
    booking_id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.property_id', ondelete='CASCADE'), nullable=False)
    renter_id = db.Column(db.Integer, db.ForeignKey('prospective_renter.renter_id', ondelete='CASCADE'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('credit_card.card_id', ondelete='RESTRICT'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    start_date = db.Column(db.Date, nullable=False)
    lease_till_date = db.Column(db.Date, nullable=False)
    
    rewards = db.relationship('Reward_program', backref='booking', lazy=True)
    
    def __repr__(self):
        return f'<Booking {self.booking_id}>'

class Reward_program(db.Model):
    __tablename__ = 'reward_program'
    
    reward_id = db.Column(db.Integer, primary_key=True)
    renter_id = db.Column(db.Integer, db.ForeignKey('prospective_renter.renter_id', ondelete='CASCADE'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.booking_id', ondelete='CASCADE'), nullable=False)
    reward_points = db.Column(db.Integer, nullable=False)
    
    def __repr__(self):
        return f'<Reward {self.reward_id}>'















