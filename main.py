import os
import threading
import time

import qrcode as qr
import qrcode.image.svg as qrsvg
from flask import Flask, redirect, render_template, request, url_for, abort, Response, session
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movieDB.sqlite"
app.config['SECRET_KEY'] = "moviecops"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
Bootstrap(app)


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


class Booking(db.Model):
    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_email = db.Column(db.String(50), db.ForeignKey(Movie.movie_id), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey(Movie.movie_id), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey(Venue.venue_id), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey(Shows.show_id), nullable=False)
    seat_num = db.Column(db.String(3), nullable=False)

    def __repr__(self):
        return f"Booking(booking_id={self.booking_id}, user_email='{self.user_email}', movie_id={self.movie_id}, " \
               f"venue_id={self.venue_id}, show_id={self.show_id}, seat_num='{self.seat_num}')"


"""
    Functions 
"""


def delete_qrcodes():
    qrFolder = os.listdir('static/qr')
    for qrCode in qrFolder:
        os.remove("static/qr/" + qrCode)


def interval_loop(interval):
    while True:
        delete_qrcodes()
        time.sleep(interval)


"""
    USER Endpoints 
"""


# USER MAIN PAGE
@app.route('/', methods=['GET', 'POST'])
def index():
    movies = db.session.query(Movie, Venue, Shows).filter(Venue.venue_id == Shows.venue_id).filter(
        Movie.movie_id == Shows.movie_id).order_by(Movie.rating.desc()).limit(6).all()

    if 'user' in session.keys():
        return render_template('index.html', userData=session['user'], recommended=movies)
    return render_template('index.html', recommended=movies)


# USER MAIN PAGE (LOCATION)
@app.route('/language/<loc>', methods=['GET', 'POST'])
def indexLang(loc):
    recommended = db.session.query(Movie, Venue, Shows).filter(Venue.venue_id == Shows.venue_id).filter(
        Movie.movie_id == Shows.movie_id, Venue.location == loc).order_by(Movie.rating.desc()).limit(6).all()
    if 'admin' in session.keys():
        return render_template('index.html', userData=session['admin'], admin=True, recommended=recommended)
    if 'user' in session.keys():
        return render_template('admin.html', userData=session['user'], recommended=recommended)
    return render_template('index.html', recommended=recommended)


# SHOWS
@app.route('/shows', methods=['GET', 'POST'])
def shows():
    movies_list = Movie.query.all()
    shows_list = Shows.query.all()
    if request.method == "POST":
        if request.form['submit'] == "search":
            searched_term = request.form['search']
            res = db.session.query(Movie, Venue, Shows).filter(Venue.venue_id == Shows.venue_id).filter(
                Movie.movie_id == Shows.movie_id).filter(Movie.name.contains(searched_term)).all()

            if 'admin' in session.keys():
                return render_template('shows.html', userData=session['admin'], search=searched_term, results=res,
                                       movies=movies_list, shows=shows_list, admin=True)
            if 'user' in session.keys():
                return render_template('shows.html', userData=session['user'], search=searched_term, results=res,
                                       movies=movies_list, shows=shows_list)
            else:
                return render_template('shows.html', search=searched_term, results=res, movies=movies_list,
                                       shows=shows_list)

        elif request.form['submit'] == "Filter":
            min_rating = request.form['minRating']
            language = request.form['language']
            location = request.form['location']

            passed = False

            query = db.session.query(Movie, Venue, Shows).filter(Venue.venue_id == Shows.venue_id).filter(
                Movie.movie_id == Shows.movie_id)

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
                res = query.all()
                if 'admin' in session.keys():
                    return render_template('shows.html', movies=movies_list, shows=shows_list, userData=session['admin'],
                                           search="Filter", results=res, admin=True)
                if 'user' in session.keys():
                    return render_template('shows.html', movies=movies_list, shows=shows_list, userData=session['user'],
                                           search="Filter", results=res)
                return render_template('shows.html', movies=movies_list, shows=shows_list, search="Filter", results=res)
            else:
                return render_template('shows.html', movies=movies_list, shows=shows_list, search="Filter")

    if 'admin' in session.keys():
        return render_template('shows.html', movies=movies_list, shows=shows_list, userData=session['admin'], admin=True)
    if 'user' in session.keys():
        return render_template('shows.html', movies=movies_list, shows=shows_list, userData=session['user'])
    return render_template('shows.html', movies=movies_list, shows=shows_list)


# USER LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user:
            return render_template('login.html', error='User not found')

        if not bcrypt.check_password_hash(user.password, password):
            return render_template('login.html', error='Invalid password')

        session['user'] = {
            "name": user.name,
            "email": user.email,
            "language": user.language
        }

        return redirect(url_for('index'))
    return render_template('login.html')


# LOGOUT
@app.route('/logout', methods=['GET'])
def logout():
    if 'user' in session:
        session.pop('user', default=None)
    return redirect(url_for('index'))


# USER SIGNUP
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        language = request.form['lang']

        check_email = User.query.filter_by(email=email).first()

        has_uppercase = False
        has_lowercase = False
        has_digit = False
        has_special = False
        allowed_special = ['!', '@', '#', '$', '%']

        if check_email:
            return render_template('signup.html', error='Email is already in use')
        if language == 'Select your preferred language':
            return render_template('signup.html', error='Select your preferred language')
        if len(password) < 8:
            return render_template('signup.html', error='Your password must have at least 8 chars')
        for char in password:
            if char.isupper():
                has_uppercase = True
            elif char.islower():
                has_lowercase = True
            elif char.isdigit():
                has_digit = True
            elif char in allowed_special:
                has_special = True
        if not (has_uppercase and has_lowercase and has_digit and has_special):
            return render_template('signup.html',
                                   error='Your password doesn\'t contain a capital letter/number/special character')

        password = bcrypt.generate_password_hash(password)
        new_user = User(email=email, name=name,
                        password=password, language=language)
        db.session.add(new_user)
        db.session.commit()

        return render_template('signup.html', success='Successfully signed up!')
    return render_template('signup.html')


# MOVIE SEAT BOOKING
@app.route('/booking/<int:show_id>', methods=['GET', 'POST'])
def booking(show_id):
    booked_seats = [x.seat_num for x in Booking.query.filter_by(show_id=show_id).all()]
    show = Shows.query.get_or_404(show_id)
    movie = Movie.query.filter_by(movie_id=show.movie_id).first()
    venue = Venue.query.filter_by(venue_id=show.venue_id).first()

    show_info = [movie.name, venue.name, venue.location, show.ticket_price]

    if request.method == "POST":

        if not ('user' in session.keys()):
            return redirect(url_for('login'))

        seats = [request.form[seat] for seat in request.form.keys()]
        return redirect((url_for('bookingConfirm', show_id=show_id, selected_seats=seats)))

    if 'admin' in session.keys():
        return render_template('seatBooking.html', userData=session['admin'], admin=True, showId=show_id, info=show_info,
                               bookedSeats=booked_seats)
    if 'user' in session.keys():
        return render_template('seatBooking.html', userData=session['user'], showId=show_id, info=show_info,
                               bookedSeats=booked_seats)

    return render_template('seatBooking.html', showId=show_id, info=show_info, bookedSeats=booked_seats)


# MOVIE SEAT CONFIRM BOOKING
@app.route('/booking/confirm/<int:show_id>', methods=['GET', 'POST'])
def bookingConfirm(show_id):
    if not ('user' in session.keys()):
        return redirect(url_for('login'))

    booked_seats = [x.seat_num for x in Booking.query.filter_by(show_id=show_id).all()]
    show = Shows.query.get_or_404(show_id)
    movie = Movie.query.filter_by(movie_id=show.movie_id).first()
    venue = Venue.query.filter_by(venue_id=show.venue_id).first()

    seats = request.args.getlist('selected_seats')

    show_info = [movie.name, venue.name, venue.location, int(show.ticket_price) * len(seats), seats, movie.image_src]

    if request.method == "POST":
        user = User.query.filter_by(email=session['user']['email']).first()

        for seat in request.form.keys():
            if request.form[seat] in booked_seats:
                abort(Response('Seat not available'))

            booked_ticket = Booking(user_email=user.email, movie_id=movie.movie_id, venue_id=venue.venue_id,
                                    show_id=show.show_id, seat_num=request.form[seat])
            db.session.add(booked_ticket)
        db.session.commit()
        return redirect(url_for('booking', show_id=show_id))

    if 'admin' in session.keys():
        return render_template('bookingConfirm.html', userData=session['admin'], admin=True, showId=show_id,
                               info=show_info,
                               seats=seats)

    return render_template('bookingConfirm.html', userData=session['user'], showId=show_id, info=show_info, seats=seats)


# USERS SHOWS
@app.route('/bookings')
def userBookings():
    if not ('user' in session.keys()):
        return redirect(url_for('login'))

    bookings = db.session.query(Booking, Movie, Venue, Shows).filter(Booking.user_email == session['user']["email"]).filter(
        Venue.venue_id == Booking.venue_id).filter(
        Movie.movie_id == Booking.movie_id).filter(Shows.show_id == Booking.show_id).all()

    details = dict()

    for b in bookings:
        if b[3].show_id not in details.keys():
            details[b[3].show_id] = {"movie_name": b[1].name, "venue_name": b[2].name, "venue_location": b[2].location,
                                     "timings": b[3].timings, "language": b[1].language, "seats": [],
                                     "image_src": b[1].image_src}

        details[b[3].show_id]["seats"].append(b[0].seat_num)

    delete_qrcodes()
    for show in details:
        data = details[show]
        factory = qrsvg.SvgImage
        qrCode = qr.make(data, image_factory=factory)
        qrCode.save(os.path.abspath(os.curdir).replace("\\", "\\\\") + "\\static\\qr\\show_" + str(show) + ".svg")

    if 'admin' in session.keys():
        return render_template('userTickets.html', userData=session['admin'], admin=True, bookings=details)

    return render_template('userTickets.html', userData=session['user'], bookings=details)


"""
    ADMIN Endpoints 
"""


# ADMIN PAGE
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not ('admin' in session.keys()):
        return redirect(url_for('index'))
    movies = db.session.query(Movie, Venue, Shows).filter(Venue.venue_id == Shows.venue_id).filter(
        Movie.movie_id == Shows.movie_id).order_by(Movie.rating.desc()).limit(6).all()

    return render_template('admin.html', userData=session['admin'], admin=True, recommended=movies)


# ADMIN LOGIN
@app.route('/admin/login', methods=['GET', 'POST'])
def adminLogin():

    if 'admin' in session.keys():
        return redirect(url_for('admin'))

    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user:
            return render_template('adminLogin.html', error='User not found')
        if not bcrypt.check_password_hash(user.password, password):
            return render_template('adminLogin.html', error='Invalid password')
        if user.email != '22f1000950@ds.study.iitm.ac.in':  # Admin User
            return render_template('login.html', error='You do not have admin privileges!')

        session['admin'] = {
            "name": user.name,
            "email": user.email,
            "language": user.language
        }

        return redirect(url_for('admin'))
    return render_template('adminLogin.html')


# ADMIN DASHBOARD (CREATE VENUES AND SHOWS)
@app.route('/admin/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not ('admin' in session.keys()):
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
    return render_template('dashboard.html', userData=session['admin'], admin=True, venues=venue_list, shows=shows_list,
                           movies=movies_list)


# ADMIN DASHBOARD (EDIT AND DELETE VENUES)
@app.route('/admin/dashboard/venue/<response>/<int:venue_id>', methods=['GET', 'POST'])
def venueRequest(response, venue_id):
    if not ('admin' in session.keys()):
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


# ADMIN DASHBOARD (EDIT AND DELETE SHOWS)
@app.route('/admin/dashboard/show/<response>/<int:show_id>', methods=['GET', 'POST'])
def showRequest(response, show_id):
    if not ('admin' in session.keys()):
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


# MAIN FUNCTION
if __name__ == '__main__':
    t = threading.Thread(target=interval_loop, args=(5,))
    t.daemon = True
    t.start()
    app.run(debug=True)
