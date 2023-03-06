from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"
db = SQLAlchemy(app)
Bootstrap(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Numeric(precision=2, scale=1), nullable=False)
    tags = db.Column(db.String(50), nullable=False)
    ticketPrice = db.Column(db.Integer, default=250, nullable=False)
    language = db.Column(db.String(50), nullable=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/shows', methods=['GET', 'POST'])
def shows():
    return render_template('shows.html')
if __name__ == '__main__':
    app.run(debug=True)