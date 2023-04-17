from .auth_forms import SignUpForm, LogInForm, UpdateProfileForm
from app.models import User
from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from app.thepokedex import Pokedex

auth = Blueprint('auth',__name__,template_folder='auth_templates')

@auth.route('/signup',methods=['GET','POST'])
def signupPage():
    form = SignUpForm()

    if request.method == 'GET':
        return render_template('signup.html',form=form)

    if not form.validate():
        return render_template('signup.html',form=form,not_valid_form=True)

    username = form.username.data.strip().lower()
    email = form.email.data
    first_name = form.first_name.data
    last_name = form.last_name.data
    password = form.password.data

    # TODO make secure password system

    email = check_email(email)
    if not email:
        return render_template('signup.html',form=form,invalid_email=True)
    
    if User.query.filter_by(username=username).first():
        return render_template('signup.html',form=form,existing_username=True)
    
    if User.query.filter_by(email=email).first():
        return render_template('signup.html',form=form,existing_email=True)


    # Instantiates user
    user = User(username, email,first_name,last_name,password)

    # Gives user random pokemon
    random_pokemon = Pokedex.pick_random_pokemon(5)
    user.setRoster(random_pokemon)

    # Saves the user to the database
    user.saveToDB()
    login_user(user)
    return redirect(url_for('homePage'))

@auth.route('/login',methods=['GET','POST'])
def loginPage():
    form = LogInForm()

    if request.method == 'GET':
        return render_template('login.html',form=form)

    if not form.validate():
        return render_template('login.html',form=form)
    
    username = form.username.data.strip().lower()
    password = form.password.data

    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        login_user(user)
        return redirect(url_for('homePage'))
    else:
        return render_template('login.html',form=form,login_issue=True)

@auth.route('/logout',methods=['GET','POST'])
def logoutUser():
    logout_user()
    return redirect(url_for('auth.loginPage'))


@auth.route('/deleteaccount',methods=['GET'])
@login_required
def deleteAccount():
    current_user.deleteFromDB()
    logout_user()
    return redirect(url_for('auth.signupPage'))

@auth.route('/update_profile',methods=['GET','POST'])
def updateProfilePage():
    form = UpdateProfileForm()
    
    if request.method == 'GET':
        return render_template("update_profile.html",form=form)
    
    error_messages = []
    if not form.validate():
        error_messages.append(("Form Did Not Validate. If you are trying to change password, make sure that you enter password twice and that they both match","danger"))
    
    
    desired_username = form.username.data.strip().lower()
    if desired_username:
        user = User.query.filter_by(username=desired_username).first()
        if not user:
            error_messages.append((f"Username successfully changed to '{desired_username}'","success"))
            current_user.username = desired_username
            current_user.saveToDB()
        elif user.username == desired_username:
            error_messages.append((f"'{desired_username}' is already your username, no need to change","success"))
        else:
            error_messages.append(("Username already taken","danger"))
            
    desired_email = form.email.data
    print(desired_email,type(desired_email))
    if desired_email:
        desired_email = check_email(desired_email)
        print(desired_email,type(desired_email))
        user_email = User.query.filter_by(email=desired_email).first()
        if not desired_email:
            error_messages.append(("Email provided is not a valid email address","danger"))
        elif not user_email:
            error_messages.append((f"Email successfully changed to '{desired_email}'","success"))
            current_user.email = desired_email
            current_user.saveToDB()
        elif user_email.email == current_user.email:
            error_messages.append((f"'{desired_email}' is already your email, no need to change","success"))
        else:
            error_messages.append(("Email address already in use by other account is not a valid email address","danger"))
            
    desired_first_name = form.first_name.data.strip()
    if desired_first_name:
        error_messages.append((f"First Name successfully changed to '{desired_first_name}'","success"))
        current_user.first_name = desired_first_name
        current_user.saveToDB()

    desired_last_name = form.last_name.data.strip()
    if desired_last_name:
        error_messages.append((f"Last Name successfully changed to '{desired_last_name}'","success"))
        current_user.last_name = desired_last_name
        current_user.saveToDB()

    desired_password = form.password.data
    if desired_password or form.confirm_password.data:
        if desired_password != form.confirm_password.data:
            error_messages.append(("Passwords did not match","danger"))
        else:
            error_messages.append((f"Password successfully changed","success"))
            current_user.password = desired_password
            current_user.saveToDB()
    
    return render_template('update_profile.html',form=form,error_messages=error_messages)

def check_email(email):
    try:
        validated = validate_email(email)
        email = validated['email']
        return email.lower()
    except EmailNotValidError as e:
        return None