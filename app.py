from flask import Flask, render_template, redirect, request, flash
from flask_login import login_required, current_user, LoginManager
from flask_login import login_user, logout_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

app = Flask(__name__)

app.config['SECRET_KEY'] = '3d_houses_very_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    username = db.Column(db.String(1000))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect('/start')
    return redirect('/login')


@app.route('/start')
@login_required
def start():
    return render_template('start.html', title='Start')

@app.route('/display_map')
@login_required
def display_map():
    return render_template('display_map.html', title='Display Map', 
        address=['Pont Roi Baudoin', '6000 Charleroi'], 
        h2={'Area': '2128m²', 'Latitude': '12345', 'Longitude': '123456'})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect('/login')
        login_user(user, remember=remember)
        return redirect('/start')
    else:
        return render_template('login.html', title='Login')


@app.route('/signup')
#@login_required
def signup():
    return render_template('signup.html')


@app.route('/signup', methods=['POST'])
#@login_required
def signup_post():

    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists')
        return redirect('/signup')

    new_user = User(email=email, username=username,
                    password=generate_password_hash(password, method='sha256'))

    db.session.add(new_user)
    db.session.commit()
    return redirect('/login')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')


if __name__ == '__main__':
    app.run()
