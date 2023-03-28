import re

from flask import Flask, redirect, render_template, request, url_for, abort, Response
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movieDB.sqlite"
db = SQLAlchemy(app)
Bootstrap(app)

logged_in = False
admin_user = False
userData = {
    "name": "",
    "email": "",
    "language": ""
}

"""
    Models for Tables
"""


class Movie(db.Model):
    movie_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    rating = db.Column(db.Numeric(precision=2, scale=1), nullable=False)
    tags = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)
    image_src = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"Movie(movie_id={self.movie_id}, name='{self.name}', rating={self.rating}, tags='{self.tags}, " \
               f" language='{self.language}, image_src='{self.image_src}')"


class User(db.Model):
    email = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"User(email='{self.email}', name='{self.name}', password='{self.password}', language='{self.language}')"


class Venue(db.Model):
    venue_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"Venue(venue_id={self.venue_id}, name='{self.name}', location='{self.location}')"


class Shows(db.Model):
    show_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    movie_id = db.Column(db.Integer, db.ForeignKey(Movie.movie_id), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey(Venue.venue_id), nullable=False)
    ticket_price = db.Column(db.Integer, default=250, nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    timings = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"Shows(show_id={self.show_id}, movie_id={self.movie_id}, venue_id={self.venue_id}, " \
               f"ticket_price={self.ticket_price}, seats={self.seats}, timings='{self.timings}')"


# class Booking(db.Model):
#     movie_id = ""
#     booking_id = ""
#     number = ""
#     venue = ""
#     timings = ""
#
#


"""
    USER Endpoints 
"""


# USER MAIN PAGE
@app.route('/', methods=['GET', 'POST'])
def index():
    if logged_in:
        return render_template('index.html', userData=userData)
    return render_template('index.html')


# LOGOUT
@app.route('/logout', methods=['GET'])
def logout():
    global logged_in, userData, admin_user
    if logged_in:
        logged_in = False
        admin_user = False
        userData = {
            "name": "",
            "email": "",
            "language": ""
        }
    return redirect(url_for('index'))


# SHOWS
@app.route('/shows', methods=['GET', 'POST'])
def shows():
    movies_list = Movie.query.all()
    if request.method == "POST":
        if request.form['submit'] == "search":
            searched_term = request.form['search']
            res = Movie.query.filter(Movie.name.contains(searched_term)).all()

            if admin_user:
                return render_template('shows.html', userData=userData, search=searched_term, results=res,
                                       movies=movies_list, admin=True)
            if logged_in:
                return render_template('shows.html', userData=userData, search=searched_term, results=res,
                                       movies=movies_list)
            else:
                return render_template('shows.html', search=searched_term, results=res, movies=movies_list)

        elif request.form['submit'] == "Filter":
            min_rating = request.form['minRating']
            language = request.form['language']
            location = request.form['location']

            passed = False

            query = db.session.query(Movie, Venue, Shows).filter(Venue.venue_id == Shows.venue_id).filter(Movie.movie_id == Shows.movie_id)

            if location != "Any":
                query = query.filter(Venue.location == location)
                passed = True
            if language != "Any":
                query = query.filter(Movie.language == language)
                passed = True
            if min_rating:
                query = query.filter(Movie.rating >= min_rating)
                passed = True

            if passed:
                res = [x[0] for x in query.all()]
                if admin_user:
                    return render_template('shows.html', movies=movies_list, userData=userData, search="Filter",
                                           results=res, admin=True)
                if logged_in:
                    return render_template('shows.html', movies=movies_list, userData=userData, search="Filter",
                                           results=res)
                return render_template('shows.html', movies=movies_list, search="Filter", results=res)
            else:
                return render_template('shows.html', movies=movies_list, search="Filter")

    if admin_user:
        return render_template('shows.html', movies=movies_list, userData=userData, admin=True)
    if logged_in:
        return render_template('shows.html', movies=movies_list, userData=userData)
    return render_template('shows.html', movies=movies_list)


# USER LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    global logged_in
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user:
            return render_template('adminLogin.html', error='User not found')
        if user.password != password:
            return render_template('adminLogin.html', error='Invalid password')

        logged_in = True

        userData["name"] = user.name
        userData["email"] = user.email
        userData["language"] = user.language

        return redirect(url_for('index'))
    return render_template('login.html')


# USER SIGNUP
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


"""
    ADMIN Endpoints 
"""


# ADMIN PAGE
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not admin_user:
        return redirect(url_for('index'))
    return render_template('admin.html', userData=userData, admin=True)


# ADMIN LOGIN
@app.route('/admin/login', methods=['GET', 'POST'])
def adminLogin():
    global logged_in, admin_user
    if admin_user:
        return redirect(url_for('admin'))

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user:
            return render_template('adminLogin.html', error='User not found')
        if user.password != password:
            return render_template('adminLogin.html', error='Invalid password')
        if user.email != 'glowstonedev@gmail.com':  # Admin User
            return render_template('login.html', error='You do not have admin privileges!')

        logged_in = True
        admin_user = True

        userData["name"] = user.name
        userData["email"] = user.email
        userData["language"] = user.language

        return redirect(url_for('admin'))
    return render_template('adminLogin.html')


# ADMIN DASHBOARD (CREATE VENUES AND SHOWS)
@app.route('/admin/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not admin_user:
        return redirect(url_for('index'))
    if request.method == "POST":
        if request.form['submit'] == "Create Venue":
            venue_name = request.form['venueName']
            venue_location = request.form['venueLocation']

            new_venue = Venue(name=venue_name, location=venue_location)
            db.session.add(new_venue)
            db.session.commit()
        if request.form['submit'] == "Add Show":
            movie_name = request.form['movieName']
            movie_rating = request.form['movieRating']
            movie_tags = request.form['movieTags']
            movie_language = request.form['movieLanguage']
            movie_image = "images/" + request.form['imageFile']

            new_movie = Movie(name=movie_name, rating=float(movie_rating), tags=movie_tags, language=movie_language,
                              image_src=movie_image)
            db.session.add(new_movie)
            db.session.commit()

            movie_timings = request.form['showTimings']
            ticket_price = request.form['ticketPrice']
            venue_id = request.form['venueId']

            new_show = Shows(movie_id=new_movie.movie_id, venue_id=venue_id, ticket_price=ticket_price, seats=50,
                             timings=movie_timings)
            db.session.add(new_show)
            db.session.commit()

    venue_list = Venue.query.all()
    shows_list = Shows.query.all()
    movies_list = Movie.query.all()
    return render_template('dashboard.html', userData=userData, admin=True, venues=venue_list, shows=shows_list,
                           movies=movies_list)


@app.route('/admin/dashboard/venue/<response>/<int:venue_id>', methods=['GET', 'POST'])
def venueRequest(response, venue_id):
    if not admin_user:
        return redirect(url_for('index'))
    if request.method == "GET":
        if response == "delete":
            venue = Venue.query.get_or_404(venue_id)

            Shows.query.filter_by(venue_id=venue.venue_id).delete()
            db.session.delete(venue)
            db.session.commit()
    if request.method == "POST":
        if response == "edit":
            venue_name = request.form['venueName']
            venue_location = request.form['venueLocation']

            venue = Venue.query.filter_by(venue_id=venue_id).first()

            if not venue:
                abort(Response('Venue Not Found'))

            venue.name = venue_name
            venue.location = venue_location

            db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/admin/dashboard/show/<response>/<int:show_id>', methods=['GET', 'POST'])
def showRequest(response, show_id):
    if not admin_user:
        return redirect(url_for('index'))
    if request.method == "GET":
        if response == "delete":
            show = Shows.query.get_or_404(show_id)
            movie = Movie.query.get_or_404(show.movie_id)
            db.session.delete(show)
            db.session.delete(movie)
            db.session.commit()
    if request.method == "POST":
        if response == "edit":
            movie_name = request.form['showName']
            movie_rating = request.form['showRating']
            movie_tags = request.form['showTags']
            movie_language = request.form['showLanguage']

            show = Shows.query.filter_by(show_id=show_id).first()
            if not show:
                abort(Response('Show Not Found'))

            movie = Movie.query.filter_by(movie_id=show.movie_id).first()

            movie.name = movie_name
            movie.rating = movie_rating
            movie.tags = movie_tags
            movie.language = movie_language

            movie_id = request.form['movieId']
            show_timings = request.form['showTimings']
            ticket_price = request.form['ticketPrice']
            venue_id = request.form['venueId']

            show.movie_id = movie_id
            show.venue_id = venue_id
            show.ticket_price = ticket_price
            show.timings = show_timings

            db.session.commit()

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
