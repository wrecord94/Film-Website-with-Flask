from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from dotenv.main import load_dotenv
import os
import requests

load_dotenv()

API_KEY_FILMS = os.environ['API_KEY_F']
API_FILMS_URL = os.environ['API_F_URL']

# Create our Database ---------------------------------- >>>>

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SUPER_SECRET_KEY']
Bootstrap5(app)

# Create our Database ---------------------------------- >>>>

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ['DB_URI']
db = SQLAlchemy()
db.init_app(app)


# Create our table model class
# CREATE TABLE
class Film(db.Model):
    film_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


# Creating the tables.
with app.app_context():
    db.create_all()


# TEST Add in a new entry ---------------------------------- >>>>

# film_test = Film(title="Phone Booth",
#                  year=2002,
#                  description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an "
#                              "extortionist's sniper rifle. Unable to leave or receive outside help, "
#                              "Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#                  rating=7.3,
#                  ranking=10,
#                  review="My favourite character was the caller.",
#                  img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg")
#
# with app.app_context():
#     db.session.add(film_test)
#     db.session.commit()


# FORM CLASSES ---------------------------------- >>>>
class RateFilmForm(FlaskForm):
    rating = StringField(label="Your Rating Out of 10 e.g. 7.5")
    review = StringField(label="Your Review")
    submit = SubmitField(label="Done")


class NewFilm(FlaskForm):
    title = StringField(label="E.g. Harry Potter", validators=[DataRequired()])
    submit = SubmitField(label="Add Film")


# Routing ---------------------------------- >>>>


@app.route("/")
def home():
    ordered_list = Film.query.order_by(Film.rating).all()
    x = 1
    for i in range(1, len(ordered_list)+1):
        ordered_list[-i].ranking = x
        x += 1

    return render_template("index.html", film_list=ordered_list)


@app.route('/edit', methods=['POST', 'GET'])
def edit():
    form = RateFilmForm()
    # Get the film ID from our URL we clicked on at homepage and stored in film_id
    film_id = request.args.get("film_id")
    # Pull out relevant film data from our database using the film_id
    film = db.get_or_404(Film, film_id)

    # 1. POST If form is filled out...
    if form.validate_on_submit():
        # Assign new db values from our form using WTF notation
        film.rating = float(form.rating.data)
        film.review = form.review.data
        # Commit changes to our database
        db.session.commit()
        # Redirect back to home
        return redirect(url_for('home'))

    # 2. GET
    # Render blank template page to then edit
    # Pass in the relevant film and our form instance to render correctly
    return render_template("edit.html", film=film, form=form)


@app.route('/delete')
def delete_entry():
    # Get the film ID from our html URL
    film_id = request.args.get("film_id")
    # Pull out relevant film data from our database using the film_id
    film_to_del = db.get_or_404(Film, film_id)
    db.session.delete(film_to_del)
    db.session.commit()
    return redirect(url_for('home'))


# if request.method == 'POST':
#     new_film = Film(title=request.form['title'])
#     db.session.add(new_film)
#     db.session.commit()
#
#     return redirect(url_for('home'))


@app.route('/add_new', methods=['GET', 'POST'])
def add_new():
    form = NewFilm()
    # Get the film title from our WTForm using the object ref notation
    film_title = form.title.data
    print(film_title)  # TEST CODE
    if form.validate_on_submit():
        film_api_response = requests.get(API_FILMS_URL, params={"api_key": API_KEY_FILMS,
                                                                "query": film_title})

        print(f"API response = {film_api_response.text}")  # TEST CODE
        film_api_data = film_api_response.json()
        list_of_results = film_api_data['results']  # Make a list out of the results to iterate through
        return render_template("select.html", list_of_results=list_of_results)
    else:
        return render_template("add.html", form=form)


@app.route('/find')
def find_film():
    # Get the film ID from our html URL
    film_id = request.args.get("film_id")
    print(film_id)  # TEST CODE
    film_responsive_url = f"https://api.themoviedb.org/3/movie/{film_id}"

    film_api_response = requests.get(film_responsive_url, params={"api_key": API_KEY_FILMS,
                                                                  "language": "en-US"})

    print(f"API response = {film_api_response.text}")  # TEST CODE
    film_api_data = film_api_response.json()
    title_add = film_api_data['original_title']
    img_url_add = f"https://image.tmdb.org/t/p/w500/{film_api_data['poster_path']}"
    year_add = film_api_data['release_date'].split("-")[0]
    desc_add = film_api_data['overview']
    # TEST CODE
    print(title_add)
    print(img_url_add)
    print(year_add)
    print(desc_add)
    # Make a new film instance from class and set attributes to above
    film_new = Film()
    film_new.title = title_add
    film_new.img_url = img_url_add
    film_new.year = year_add
    film_new.description = desc_add
    # Add new film to db
    db.session.add(film_new)
    # Commit changes to our database
    db.session.commit()

    return redirect(url_for('edit', film_id=film_new.film_id))


# Pass the ID as film_id to the find_page and make API call.
# API call
# THEN once done redirect to homepage..

if __name__ == '__main__':
    app.run(debug=True)


