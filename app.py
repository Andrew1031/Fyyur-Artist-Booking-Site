#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
from time import strftime
from datetime import datetime
import dateutil.parser
import babel
from flask import (
  Flask,
  render_template,
  request,
  Response,
  flash,
  redirect,
  url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from models import db, Venue, Artist, Show
import flask_wtf
from flask_wtf.csrf import CSRFProtect
import config
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
moment = Moment(app)
db.init_app(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  cities = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)
  venues = Venue.query.group_by(Venue.id, Venue.city, Venue.state).all()

  for city in cities:
    venuesData = []
    cityName = city[0]
    stateName = city[1]

    for venue in venues:
      if venue.city == cityName:
        venuesData.append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": db.session.query(Show).filter(Show.venue_id==venue.id).filter(Show.start_time>datetime.now()).count()
        })

    data.append({
      "city": cityName,
      "state": stateName,
      "venues": venuesData
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term')
  searchResults = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()
  data = []

  for searchResult in searchResults:
    data.append({
      "id": searchResult.id,
      "name": searchResult.name,
      "num_upcoming_shows": db.session.query(Show).filter(Show.venue_id==searchResult.id).filter(Show.start_time>datetime.now()).count()
    })

  response = {}
  response['count'] = len(data)
  response['data'] = data

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  past_shows = []
  upcoming_shows = []
  shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).order_by(Show.start_time)
  for show in shows:
    show.venue = Venue.query.filter_by(id=show.venue_id).first_or_404()
    show.artist = Artist.query.filter_by(id=show.artist_id).first_or_404()
    showAppend = {
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time.strftime("%m/%d/%Y, %H:%M"))
    }

    if (str(show.start_time.strftime("%m/%d/%Y, %H:%M")) < str(datetime.now().strftime("%m/%d/%Y, %H:%M"))):
      past_shows.append(showAppend)

    else:
      upcoming_shows.append(showAppend)

  data = {
    "id": venue_id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  error = False
  form = VenueForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      name = form.name.data
      city = form.city.data
      state = form.state.data
      address = form.address.data
      phone = form.phone.data
      image_link = form.image_link.data
      genres = form.genres.data
      facebook_link = form.facebook_link.data
      website_link = form.website_link.data
      seeking_talent = form.seeking_talent.data
      seeking_description = form.seeking_description.data
      venue = Venue(name=name, city=city, state=state, address=address, phone=phone, image_link=image_link,
                    genres=genres, facebook_link=facebook_link, website=website_link, seeking_talent=seeking_talent,
                    seeking_description=seeking_description)
      db.session.add(venue)
      db.session.commit()

    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

    finally:
      db.session.close()
      # on successful db insert, flash success
      if error == False:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    toDelete = Venue.query.get(venue_id)
    deletedName = toDelete.name
    db.session.delete(Venue.query.get(toDelete))
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    flash('Error: ' + deletedName + ' could not be deleted')
  finally:
    db.session.close()

  flash(deletedName + ' was successfully deleted')

  # BONUS CHALLENGE: Implement a button to de lete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  artists = Artist.query.with_entities(Artist.id, Artist.name).all()

  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term')
  searchResults = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()
  data = []

  for searchResult in searchResults:
    data.append({
      "id": searchResult.id,
      "name": searchResult.name,
      "num_upcoming_shows": db.session.query(Show).filter(Show.artist_id == searchResult.id).filter(
        Show.start_time > datetime.now()).count()
    })

  response = {}
  response['count'] = len(data)
  response['data'] = data

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist = Artist.query.get(artist_id)
  past_shows = []
  upcoming_shows = []
  shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).order_by(Show.start_time)
  for show in shows:
    show.venue = Venue.query.filter_by(id=show.venue_id).first_or_404()
    show.artist = Artist.query.filter_by(id=show.artist_id).first_or_404()
    showAppend = {
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": str(show.start_time.strftime("%m/%d/%Y, %H:%M"))
    }

    if (str(show.start_time.strftime("%m/%d/%Y, %H:%M")) < str(datetime.now().strftime("%m/%d/%Y, %H:%M"))):
      past_shows.append(showAppend)

    else:
      upcoming_shows.append(showAppend)

  data = {
    "id": artist_id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  # TODO: populate form with fields from artist with ID <artist_id>
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(obj=artist)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  form = ArtistForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.phone = form.phone.data
      artist.image_link = form.image_link.data
      artist.genres = form.genres.data
      artist.facebook_link = form.facebook_link.data
      artist.website_link = form.website_link.data
      artist.seeking_venue = form.seeking_venue.data
      artist.seeking_description = form.seeking_description.data
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Artist ' + request.name + ' could not be edited.')
    finally:
      db.session.close()
      # on successful db insert, flash success
      if error == False:
        flash('Artist ' + form.name.data + ' was successfully edited!')
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  # TODO: populate form with values from venue with ID <venue_id>
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(obj=venue)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  form = VenueForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.phone = form.phone.data
      venue.image_link = form.image_link.data
      venue.genres = form.genres.data
      venue.facebook_link = form.facebook_link.data
      venue.website_link = form.website_link.data
      venue.seeking_talent = form.seeking_talent.data
      venue.seeking_description = form.seeking_description.data
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Venue ' + request.name + ' could not be edited.')
    finally:
      db.session.close()
      # on successful db insert, flash success
      if error == False:
        flash('Venue ' + form.name.data + ' was successfully edited!')
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  error = False
  form = ArtistForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      name = form.name.data
      city = form.city.data
      state = form.state.data
      phone = form.phone.data
      image_link = form.image_link.data
      genres = form.genres.data
      facebook_link = form.facebook_link.data
      website_link = form.website_link.data
      seeking_venue = form.seeking_venue.data
      seeking_description = form.seeking_description.data
      artist = Artist(name=name, city=city, state=state, phone=phone, image_link=image_link,
                    genres=genres, facebook_link=facebook_link, website=website_link, seeking_venue=seeking_venue,
                    seeking_description=seeking_description)
      db.session.add(artist)
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Artist ' + request.name + ' could not be listed.')
    finally:
      db.session.close()
      # on successful db insert, flash success
      if error == False:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))


  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  shows = Show.query.order_by(Show.start_time).all()

  for show in shows:
    if show.start_time > datetime.now():
      show.venue = Venue.query.filter_by(id=show.venue_id).first_or_404()
      show.artist = Artist.query.filter_by(id=show.artist_id).first_or_404()
      data.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": str(show.start_time.strftime("%m/%d/%Y, %H:%M"))
      })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  form = ShowForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      artist_id = form.artist_id.data
      venue_id = form.venue_id.data
      start_time = form.start_time.data
      show = Show(artist_id = artist_id, venue_id=venue_id, start_time=start_time)
      db.session.add(show)
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Show could not be listed.')
    finally:
      db.session.close()
      # on successful db insert, flash success
      if error == False:
        flash('Show was successfully listed!')
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
