from .auth_forms import SignUpForm, LogInForm
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


@auth.route('/deleteaccount',methods=['GET','POST'])
@login_required
def deleteAccount():
    current_user.deleteFromDB()
    logout_user()
    return redirect(url_for('auth.signupPage'))


def check_email(email):
    try:
        validated = validate_email(email)
        email = validated['email']
        return email.lower()
    except EmailNotValidError as e:
        return None