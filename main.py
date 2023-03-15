from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"
db = SQLAlchemy(app)
Bootstrap(app)

# models for tables
loggged_in = False


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Numeric(precision=2, scale=1), nullable=False)
    tags = db.Column(db.String(50), nullable=False)
    ticketPrice = db.Column(db.Integer, default=250, nullable=False)
    language = db.Column(db.String(50), nullable=False)


class User(db.Model):
    email = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    mobile_no = db.Column(db.Integer, nullable=False, unique=True)
    language = db.Column(db.String(50), nullable=False)


with app.app_context():
    db.create_all()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        searched_term = request.form['search']
        return render_template('shows.html', search=searched_term)
    return render_template('index.html')


@app.route('/shows', methods=['GET', 'POST'])
def shows():
    return render_template('shows.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        print(request.data)
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if not user:
            return render_template('login.html', error='User not found')
        if user.password != password:
            return render_template('login.html', error='Invalid password')
        global logged_in
        logged_in = True
        return render_template('index.html')
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)
