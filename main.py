import re

from flask import Flask, redirect, render_template, request, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movieDB.sqlite"
db = SQLAlchemy(app)
Bootstrap(app)

logged_in = False
userData = {
    "name": "",
    "email": "",
    "language": ""
}


# Models for tables
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Numeric(precision=2, scale=1), nullable=False)
    tags = db.Column(db.String(50), nullable=False)
    ticketPrice = db.Column(db.Integer, default=250, nullable=False)
    language = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"Movie(id={self.id}, name='{self.name}', rating={self.password}, tags='{self.tags}, " \
               f"ticketPrice={self.ticketPrice}, language='{self.language}')"


class User(db.Model):
    email = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"User(email='{self.email}', name='{self.name}', password='{self.password}', language='{self.language}')"


@app.route('/', methods=['GET', 'POST'])
def index():
    if logged_in:
        print(userData)
        return render_template('index.html', name=userData["name"])
    if request.method == "POST":
        searched_term = request.form['search']
        return render_template('shows.html', search=searched_term)
    return render_template('index.html')


@app.route('/shows', methods=['GET', 'POST'])
def shows():
    return render_template('shows.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global logged_in
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user:
            return render_template('login.html', error='User not found')
        if user.password != password:
            return render_template('login.html', error='Invalid password')

        logged_in = True

        userData["name"] = user.name
        userData["email"] = user.email
        userData["language"] = user.language

        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        language = request.form['lang']

        check_email = User.query.filter_by(email=email).first()

        if check_email:
            return render_template('signup.html', error='Email is already in use')
        if language == 'Select your preferred language':
            return render_template('signup.html', error='Select your preferred language')
        if len(password) < 8:
            return render_template('signup.html', error='Your password must have at least 8 chars')
        if bool(re.match('^[a-zA-Z0-9]*$', password)):
            return render_template('signup.html',
                                   error='Your password doesn\'t contain a capital letter/number/special character')

        new_user = User(email=email, name=name,
                        password=password, language=language)
        db.session.add(new_user)
        db.session.commit()

        return render_template('signup.html', success='Successfully signed up!')
    return render_template('signup.html')


if __name__ == '__main__':
    app.run(debug=True)
