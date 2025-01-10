from controllers.database import db
from datetime import datetime

# Base User model, which both Customer and ServiceProfessional will inherit
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(15), nullable=False) 
    is_active = db.Column(db.Boolean, default=True) 

class Admin(User):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

# Service Professional model
class ServiceProfessional(db.Model):
    __tablename__ = 'service_professionals'
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    service_type = db.Column(db.String(50), nullable=False) 
    experience = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    doc_url = db.Column(db.String(200), nullable=True) 
    is_approved = db.Column(db.Boolean, default=False) 
    reviews = db.relationship('Review', backref='professional', lazy=True)
    is_complete = db.Column(db.Boolean, default=False) 

# Customer model
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, db.ForeignKey('users.id'),primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    service_requests = db.relationship('ServiceRequest', backref='customer', lazy=True)

# Service model
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    time_required = db.Column(db.Integer, nullable=False)  # Time in minutes/hours
    description = db.Column(db.Text)

# Service Request model
class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professionals.id'))
    date_of_request = db.Column(db.DateTime, default=datetime.utcnow)
    date_of_completion = db.Column(db.DateTime)
    service_status = db.Column(db.String(20), default='requested')  # requested, assigned, closed
    service = db.relationship('Service', backref=db.backref('requests', lazy=True))
    professional = db.relationship('ServiceProfessional', backref=db.backref('service_requests', lazy=True))
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id'), nullable=True)
    review = db.relationship('Review', backref='service_request', uselist=False)

# Review model for customers reviewing service professionals
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professionals.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # Rating out of 5
    comments = db.Column(db.Text)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    customer = db.relationship('Customer', backref='reviews')
    date_of_review = db.Column(db.DateTime, default=datetime.utcnow)


