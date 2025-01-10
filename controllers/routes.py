from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from controllers.model import db, Admin, Customer, ServiceProfessional, Service, ServiceRequest, User, Review
from datetime import datetime
from flask import jsonify, request

main = Blueprint('main', __name__)

@main.route('/logout')
def logout():
    session.pop('user_id', None) 
    return redirect(url_for('main.login'))

@main.route('/')
def index():
    return redirect(url_for('main.login')) 

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(f"Creating user with Username: {username}, Password: {password}")
        user = db.session.query(User).filter_by(username=username, password=password).first()
        print(user)
        
        # Check if user exists
        if user is not None:  # Correct way to check if the user is found
            session['user_id'] = user.id
            session['user_role'] = user.role
            if user.role == 'PROFESSIONAL':
                return redirect(url_for('main.serviceprofessional_dashboard'))
            elif user.role == 'CUSTOMER':
                return redirect(url_for('main.customer_dashboard'))
            else:
                return redirect(url_for('main.admin_dashboard'))
        else:
            # Set a flash message for failed login attempt
            flash('User credentials are incorrect. Please try again.', 'error')
            return redirect(url_for('main.login'))  # Redirect to login page to show the message
    
    return render_template('login.html')


# Route for registration page


@main.route('/register/customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        address = request.form.get('address')
        role = 'CUSTOMER'

        # Debugging output
        print(f"Request method: {request.method}")
        print(f"Creating user with Username: {username}, Email: {email}, Password: {password}, Role: {role}")
        print(f"Form data: {request.form}")

        # Validate inputs
        if not username or not email or not password or not name or not address:
            flash('Please fill in all fields.')
            return redirect(url_for('main.register_customer'))

        # Check if the user already exists
        existing_user = db.session.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists. Please choose a different one.')
            return redirect(url_for('main.register_customer'))

        # Create a new user in the database
        new_user = User(username=username, email=email, password=password, role=role)
        db.session.add(new_user)

        try:
            db.session.commit()  # Attempt to commit the new user
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            print(f"Error committing user: {e}")  # Debugging error
            flash('An error occurred while registering. Please try again.')
            return redirect(url_for('main.register_customer'))

        # Create a customer entry
        customer = Customer(id=new_user.id, name=name, address=address)
        db.session.add(customer)

        try:
            db.session.commit()  # Attempt to commit the new customer
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            print(f"Error committing customer: {e}")  # Debugging error
            flash('An error occurred while creating your profile. Please try again.')
            return redirect(url_for('main.register_customer'))

        flash('Registration successful! You can now log in.')
        return redirect(url_for('main.login'))

    return render_template('register_customer.html')



@main.route('/register/professional', methods=['GET', 'POST'])
def register_professional():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        service_type = request.form.get('service_type')
        experience = request.form.get('experience')
        desc = request.form.get('desc')
        doc_url = request.form.get('doc_url')
        role = 'PROFESSIONAL'

        # Validate inputs
        if not username or not email or not password or not name or not service_type or not experience:
            flash('Please fill in all fields.')
            return redirect(url_for('main.register_professional'))

        # Check if the user already exists
        existing_user = db.session.query(User).filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.')
            return redirect(url_for('main.register_professional'))

        # Create a new user in the database
        new_user = User(username=username, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        # Create a service professional entry
        professional = ServiceProfessional(id=new_user.id, name=name, service_type=service_type,
                                           experience=experience, doc_url=doc_url, description=desc)
        db.session.add(professional)
        db.session.commit()

        flash('Registration successful! You can now log in.')
        return redirect(url_for('main.login'))

    # Fetch available services for the dropdown
    services = Service.query.all()
    return render_template('register_professional.html', services=services)


@main.route('/admin/dashboard')
def admin_dashboard():
    # Query the database for professionals who are not approved
    professional_requests = ServiceProfessional.query.filter_by(is_approved=False).all()
    services = Service.query.with_entities(Service.name).all()
    service_names = [service[0] for service in services]
    blocked_users = User.query.filter_by(is_active=False).all()
    return render_template('admin_dashboard.html', professional_requests=professional_requests,services=service_names,blocked_users=blocked_users)

@main.route('/unblock_user', methods=['POST'])
def unblock_user():
    user_id = request.form['user_id']
    # Logic to unblock the user in the database
    user = User.query.get(user_id)
    if user:
        user.is_active = True
        db.session.commit()
    return redirect(url_for('main.admin_dashboard'))


@main.route('/professional/dashboard')
def serviceprofessional_dashboard():
    current_user_id = session.get('user_id')  # Get the current user's ID from the session
    #print(current_user_id)
    #user = ServiceProfessional.query.get(current_user_id)
    #print(user)
    user1 = (
        db.session.query(ServiceProfessional, User)
        .join(User, User.id == ServiceProfessional.id)  # Join with User
        .filter(ServiceProfessional.id==current_user_id)  # Case-insensitive search
        .all()
    )
    print(user1)
    services = Service.query.with_entities(Service.name).all()
    print(services)
    service_names = [service[0] for service in services]
    return render_template('serviceprofessional_dashboard.html', users=user1,services=service_names)  # Pass the full user object to the template


# Route for managing services
@main.route('/admin/services', methods=['GET', 'POST'])
def services():
    if request.method == 'POST':
        # Handle adding a new service
        if 'name' in request.form:  # Check if adding a service
            name = request.form['name']
            price = request.form['price']
            time_required = request.form['time_required']
            description = request.form['description']
            new_service = Service(name=name, price=price, time_required=time_required, description=description)
            db.session.add(new_service)
            db.session.commit()
            flash('Service added successfully!')
            return redirect(url_for('main.services'))
        
        # Handle searching for services
        search_query = request.form.get('search_query')
        services = Service.query.filter(Service.name.contains(search_query)).all()
        if search_query=='all':
            services = Service.query.all()
    else:
        services = Service.query.all()
    return render_template('services.html', services=services)

# Route for handling service requests

@main.route('/search', methods=['POST'])
def search():
    search_query = request.form.get('search_query')
    search_query = search_query.lower()
    professionals = (
        db.session.query(ServiceProfessional, User)
        .join(User, User.id == ServiceProfessional.id)  # Join with User
        .filter(ServiceProfessional.name.ilike(f'%{search_query}%'))  # Case-insensitive search
        .all()
    )
    return render_template('all_approved_professionals.html', professionals=professionals, title='Search Results')



@main.route('/admin/service_requests', methods=['GET', 'POST'])
def service_requests():
    current_user_id = session.get('user_id')  
    requests = ServiceRequest.query.filter_by(professional_id=current_user_id).all() 
    return render_template('service_requests.html', requests=requests)  


@main.route('/customer/dashboard', methods=['GET', 'POST'])
def customer_dashboard():
    current_user_id = session.get('user_id')
    services = Service.query.all()
    requests = ServiceRequest.query.filter_by(customer_id=current_user_id).all()
    reviews = Review.query.filter_by(customer_id=current_user_id).all()
    user = User.query.filter_by(id=current_user_id).first()
    selected_service_id = None

    if request.method == 'POST':
        selected_service_id = request.form.get('service_id')
        if selected_service_id:
            selected_service_id = int(selected_service_id)
            print(selected_service_id)
            professionals = (
                db.session.query(ServiceProfessional)
                .join(User, User.id == ServiceProfessional.id)
                .filter(
                    ServiceProfessional.is_approved == True,
                    User.is_active == True,
                    ServiceProfessional.service_type == Service.query.get(selected_service_id).name
                )
                .all()
            )
        else:
            professionals = (
                db.session.query(ServiceProfessional)
                .join(User, User.id == ServiceProfessional.id)
                .filter(
                    ServiceProfessional.is_approved == True,
                    User.is_active == True
                )
                .all()
            )
    else:
        professionals = (
            db.session.query(ServiceProfessional)
            .join(User, User.id == ServiceProfessional.id)
            .filter(
                ServiceProfessional.is_approved == True,
                User.is_active == True
            )
            .all()
        )

    return render_template('customer_dashboard.html', services=services, requests=requests, reviews=reviews, user=user, professionals=professionals, selected_service_id=selected_service_id)

@main.route('/book_service/<int:professional_id>', methods=['POST'])
def book_service(professional_id):
    service_id = request.form.get('service_id')
    customer_id = session.get('user_id')
    print(service_id)
    service_id=int(service_id)
    service_ids = Service.query.with_entities(Service.id).all()
    service_id_list = [service_id[0] for service_id in service_ids]
    print(service_id_list)
    existing_request = ServiceRequest.query.filter_by(
        customer_id=customer_id,
        professional_id=professional_id
    ).first()
    if existing_request:
        flash("You have already booked this professional. You cannot book again.")
        return redirect(url_for('main.customer_dashboard'))  # Redirect to the relevant page
    if service_id not in service_id_list:
       flash('Please select a service before booking.', 'error')
       print(type(service_id))
       print(type(service_id_list[0]))
       return redirect(url_for('main.customer_dashboard'))
      
    
    new_request = ServiceRequest(professional_id=professional_id, customer_id=customer_id, service_id=service_id, service_status='Pending')
    db.session.add(new_request)
    db.session.commit()
    flash('Service booked successfully!')
    return redirect(url_for('main.customer_dashboard'))

@main.route('/delete_request/<int:request_id>', methods=['POST'])
def delete_request(request_id):
    current_user_id = session.get('user_id')
    
    request_to_delete = ServiceRequest.query.filter_by(customer_id=current_user_id, id=request_id, service_status='Pending').first()
    if request_to_delete:
        db.session.delete(request_to_delete)
        db.session.commit()
        flash('Request deleted successfully!')
    else:
        flash('No pending request found to delete.')
    
    return redirect(url_for('main.customer_dashboard'))

@main.route('/requests', methods=['GET'])
def requests():
    current_user_id = session.get('user_id')  # Get the current user's ID from the session
    requests = ServiceRequest.query.filter_by(customer_id=current_user_id).all()  # Fetch all requests for the current user
    print(requests)
    return render_template('requests.html', requests=requests)  # Render a new template with the requests

@main.route('/accept_request/<int:request_id>', methods=['POST'])
def accept_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    service_request.service_status = 'accepted'
    db.session.commit()
    flash('Request accepted successfully.')
    return redirect(url_for('main.service_requests'))

@main.route('/complete_request/<int:request_id>', methods=['POST'])
def complete_request(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    service_request.service_status = 'complete'
    db.session.commit()
    flash('Request marked as complete.')
    return redirect(url_for('main.service_requests'))

@main.route('/delete_request/<int:request_id>', methods=['POST'])
def delete(request_id):
    service_request = ServiceRequest.query.get_or_404(request_id)
    # Change status to rejected instead of deleting
    service_request.service_status = 'rejected'
    db.session.commit()
    flash('Request has been rejected.')
    return redirect(url_for('main.service_requests'))



@main.route('/customer/past_reviews')
def past_reviews():
    current_user= session.get('user_id')
    reviews = Review.query.filter_by(customer_id=current_user).all()
    return render_template('past_review.html', reviews=reviews)


@main.route('/leave_review/<int:professional_id>', methods=['GET', 'POST'])
def leave_review(professional_id):
    customer_id = session.get('user_id')  # Get the customer ID from the session
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        # Ensure all fields are filled
        if not rating or not comment:
            flash('Please provide both a rating and a comment.')
            return redirect(url_for('main.leave_review', professional_id=professional_id))

        # Create a new review in the database
        new_review = Review(professional_id=professional_id, customer_id=customer_id, rating=rating, comments=comment, date_of_review=datetime.now())
        db.session.add(new_review)
        db.session.commit()

        # Update the corresponding service request with the review_id
        service_request = ServiceRequest.query.filter_by(customer_id=customer_id, professional_id=professional_id).first()

        if service_request:
            service_request.review_id = new_review.id
            db.session.commit()

        flash('Your review has been submitted!')
        return redirect(url_for('main.customer_dashboard'))

    # Render the review form if the method is GET
    return render_template('leave_review.html', professional_id=professional_id)


@main.route('/review/edit/<int:review_id>', methods=['GET', 'POST'])
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)

    if request.method == 'POST':
        # Get form data from the POST request
        new_rating = request.form.get('rating')
        new_comments = request.form.get('comments')

        # Update the review
        review.rating = new_rating
        review.comments = new_comments
        db.session.commit()

        flash('Your review has been updated!', 'success')
        return redirect(url_for('main.past_reviews'))  # Redirect to the past reviews page

    # If GET request, render the edit review form
    return render_template('edit_review.html', review=review)


@main.route('/request/delete/<int:request_id>', methods=['POST'])
def delete_c_request(request_id):
    # Fetch the customer request by id
    customer_request = ServiceRequest.query.get_or_404(request_id)

    if customer_request:
        customer_request.service_status = 'Rejected'
        db.session.commit()

        flash('The request has been rejected', 'success')
    else:
        flash('Request not found.', 'danger')

    return redirect(url_for('main.service_requests')) 

@main.route('/delete_review/<int:review_id>', methods=['POST'])
def delete_review(review_id):
    # Fetch the review by its ID
    review = Review.query.get_or_404(review_id)

    # Find the related service request and remove the review_id from it
    service_request = ServiceRequest.query.filter_by(review_id=review_id).first()
    if service_request:
        service_request.review_id = None  # Remove the reference to the review

    # Delete the review from the database
    db.session.delete(review)
    db.session.commit()

    flash('Review has been deleted successfully.')
    return redirect(url_for('main.customer_dashboard'))


@main.route('/admin/update_approval_status', methods=['POST'])
def update_approval_status():
    data = request.form  # Access form data from the POST request
    request_id = data.get('request_id')
    is_approved = data.get('is_approved') == 'approved'  # Convert the value to a boolean

    # Find the professional request in the database by its ID
    professional_request = ServiceProfessional.query.get(request_id)
    
    if not professional_request:
        flash('Professional request not found.', 'danger')
        return redirect(url_for('main.admin_dashboard'))

    # Update the approval status
    professional_request.is_approved = is_approved
    db.session.commit()

    flash('Approval status updated successfully.', 'success')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    service = Service.query.get(service_id)
    
    if not service:
        flash('Service not found.', 'danger')
        return redirect(url_for('main.services'))

    if request.method == 'POST':
        # Get updated values from the form
        service.name = request.form['name']
        service.price = request.form['price']
        service.time_required = request.form['time_required']
        service.description = request.form['description']

        db.session.commit()
        flash('Service updated successfully.', 'success')
        return redirect(url_for('main.services'))

    return render_template('edit_service.html', service=service)

@main.route('/admin/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    # Find the service to delete
    service_to_delete = Service.query.get_or_404(service_id)

    # Get all professionals associated with this service
    professionals = ServiceProfessional.query.filter_by(service_type=service_to_delete.name).all()

    # Cancel all pending requests for this service
    pending_requests = ServiceRequest.query.filter_by(service_id=service_id, service_status='Pending').all()

    for request in pending_requests:
        request.service_status = 'Canceled'  # Change the status to 'Canceled'
        db.session.commit()

    # Notify professionals
    for professional in professionals:
        # Here you could store messages in a notification system or use flash messages.
        flash(f'The service "{service_to_delete.name}" no longer exists. Your pending requests for this service have been canceled.', 'warning')

    # Delete the service from the database
    db.session.delete(service_to_delete)
    db.session.commit()

    flash('Service deleted successfully!')
    return redirect(url_for('main.services'))


@main.route('/service/update/<int:service_id>', methods=['POST'])
def update_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.name = request.form['name']
    service.price = request.form['price']
    service.time_required = request.form['time_required']
    service.description = request.form['description']

    db.session.commit()
    flash('Service updated successfully!', 'success')
    return redirect(url_for('main.services'))

@main.route('/customers')
def all_customers():
    customers = User.query.filter_by(role='CUSTOMER', is_active=True).all()
    return render_template('all_customer.html', customers=customers)

@main.route('/approved_professionals')
def all_approved_professionals():
    # Querying the approved professionals who are active in the users table
    professionals = (
        db.session.query(ServiceProfessional, User)
        .join(User, User.id == ServiceProfessional.id)
        .filter(ServiceProfessional.is_approved == True, User.is_active == True)
        .all()
    )
    print(professionals)
    return render_template('all_approved_professionals.html', professionals=professionals, title='Approved Professionals')


@main.route('/remove_user/<int:user_id>', methods=['POST'])
def remove_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_active = False
        db.session.commit()
        flash('User has been removed successfully.')
    else:
        flash('User not found.')
    return redirect(url_for('main.admin_dashboard'))