from flask import Flask, render_template, redirect, request, flash
from flask_login import login_required, current_user, LoginManager
from flask_login import login_user, logout_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
from os import path, environ
from becode3d.map_creation import Location
from becode3d.variables import DATAS
from becode3d.functions import lambert_to_wgs
import pickle

app = Flask(__name__)
app.config['SECRET_KEY'] = environ['SECRET_KEY']
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
    # Login Disabled, redirect to start
    return redirect('/start')


@app.route('/start')
# @login_required
def start():
    flash('In order to save valuable disk space, only the province of Liège is covered.')
    return render_template('start.html', title='Start')

@app.errorhandler(500)
def address_not_found(e):
    flash('Address NOT FOUND :)')
    return redirect('/start')

@app.route('/display_map')
# @login_required
def display_map():
    flash('Kindly start with a search :)')
    return redirect('/start')

@app.route('/display_map', methods=['POST'])
# @login_required
def display(searchterm='', range_value=''):
    json = {'found': True}
    if request.method == 'POST':
        searchterm = request.form.get('searchterm')
        range_value = request.form.get('range_value')
    instance = Location(searchterm, int(range_value))
    cached = f'./templates/maps/{instance.x}x{instance.y}y{instance.boundary}.html'
    if path.exists(cached):
        with open(cached) as file:
            html_map = file.read()
        with open(f'{cached}pickle', 'rb') as handle:
            features = pickle.load(handle)
    else:
        instance.find_files()
        instance.create_chm()
        html_map, features = instance.create_plotly_map()
    if json['found'] == False:
        flash('No results found, please try again.')
        return redirect('/start')
    hits = []
    for feature in features:
        try: 
            hits.append({'Length': f"{round(feature[1]['properties']['SHAPE_Length'], 2)} m.",
                         'Area':   f"{round(feature[1]['properties']['SHAPE_Area'], 2)} m.²",
                         'Hauteur Toit': f"{round(feature[1]['properties']['E_TOIT'], 2)} m."})
        except KeyError:
            pass
    print('TOTAL FEATURES LOADED', len(hits))
    return render_template('display_map.html', title=f'{len(features)}: Display Map', 
        address=instance.address, h2={'Select the CONTOUR': 'for building infos 🏠'}, html_map=html_map, hits=hits, )

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


# @login_required
@app.route('/signup')
def signup():
    return render_template('signup.html')


# @login_required
@app.route('/signup', methods=['POST'])
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
  port = int(environ.get('PORT', 5000))
  app.run(host = '0.0.0.0', port = port)