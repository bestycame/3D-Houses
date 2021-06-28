from flask import Flask, render_template, redirect, request, flash
from flask_login import login_required, current_user, LoginManager
from flask_login import login_user, logout_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

app = Flask(__name__)

app.config['SECRET_KEY'] = 'future_of_living'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

# data = pd.read_csv(
#     'gs://future_of_living_storage_beatfr/data/_csv/predictions.csv')


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


# @app.route('/ccn', methods=['POST'])
# @app.route('/ccn/<searchterm>')
# @login_required
# def ccnpage(searchterm=''):
#     if request.method == 'POST':
#         searchterm = request.form.get('searchterm')
#     json = updateccn(searchterm)
#     if json['found'] == False:
#         flash('No results found, please try again.')
#         return redirect('/start')
#     return render_template('ccn.html',
#                            h1=json['h1'],
#                            h2=json['h2'],
#                            title='CCN')


# @app.route('/updateccn/<searchterm>')
# @login_required
# def updateccn(searchterm):
#     try:
#         searchterm = int(searchterm)
#     except ValueError:
#         searchterm = searchterm

#     if data[data['community_id'] == searchterm].shape[0] != 0:
#         city = data[data['community_id'] == searchterm]
#     elif data[data['zip_code'] == searchterm].shape[0] != 0:
#         city = data[data['zip_code'] == searchterm]
#     elif data[data['community_name'] == searchterm].shape[0] != 0:
#         city = data[data['community_name'] == searchterm]
#     else:
#         return {'found': False}
#     h1 = {'ID': city['community_id'].item(),
#           'Name': city['community_name'].item(),
#           'ZIP': city['zip_code'].item()}
#     h2 = {'Projected yearly recoup':
#           f"{round(city['KPI'].item()*100, 2)} %",
#           'Estimated Rent Prices':
#           f"{round(city['average_overall_sqm_price'].item(), 2)} € / m²",
#           'Avg Property Price':
#           f"{round(city['property_land_price_m2'].item(), 2)} € / m²",
#           'Distance from Nearest Capital':
#           f"{int(city['travel_distance_to_hub_in_km'].item())} km / {int(city['travel_duration_to_hub_in_min'].item())} min"}
#     order = ['Projected yearly recoup', 'Estimated Rent Prices', 'Avg Property Price', 'Distance from Nearest Capital']
#     return {'found': True, 'h1': h1, 'h2': h2, 'order':order}


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
