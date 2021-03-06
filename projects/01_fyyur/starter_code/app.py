#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import func
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATION']=True
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *
# class Venue(db.Model):
#     __tablename__ = 'Venue'

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120))
#     city = db.Column(db.String(120))
#     state = db.Column(db.String(120))
#     address = db.Column(db.String(120))
#     phone = db.Column(db.String(120))
#     genres = db.Column(db.String(120))
#     image_link = db.Column(db.String(500))
#     facebook_link = db.Column(db.String(120))
    
#     # TODO: implement any missing fields, as a database migration using Flask-Migrate
#     genres = db.Column(db.String(120),nullable=False)
#     website_link = db.Column(db.String(120))
#     seeking_talent = db.Column(db.Boolean,default=False)
#     seeking_description = db.Column(db.String(1000))
#     shows = db.relationship('Show',backref='venue',lazy=True, cascade="all, save-update, merge, delete, delete-orphan")

# class Artist(db.Model):
#     __tablename__ = 'Artist'
 
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(120))
#     city = db.Column(db.String(120))
#     state = db.Column(db.String(120))
#     phone = db.Column(db.String(120))
#     genres = db.Column(db.String(120))
#     image_link = db.Column(db.String(500))
#     facebook_link = db.Column(db.String(120))

#     # TODO: implement any missing fields, as a database migration using Flask-Migrate
#     website_link = db.Column(db.String(120))
#     seeking_venue = db.Column(db.Boolean, default=False)
#     seeking_description = db.Column(db.String(1000))
#     shows = db.relationship('Show',backref='artist',lazy=True, cascade="save-update, merge, delete")

# # TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
# class Show(db.Model):
#     __tablename__ = 'shows'
#     id = db.Column(db.Integer, primary_key=True)
#     start_time = db.Column(db.DateTime, nullable=False)
#     artist_id = db.Column(db.Integer,db.ForeignKey('Artist.id') ,nullable=False)
#     venue_id = db.Column(db.Integer,db.ForeignKey('Venue.id') ,nullable=False)
    

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
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  current_time = datetime.now()
  venue_areas = Venue.query.distinct(Venue.state, Venue.city).all()
  data = []
  for area in venue_areas:
    city_state= {
      'city':area.city,
      'state':area.state
      
      }
    venues = Venue.query.filter_by(city = area.city, state = area.state).all()
    venues_list=[]
    for venue in venues:
      venues_list.append({
        'id': venue.id,
        'name': venue.name,
        'upcoming_shows': len(list(filter(lambda venue_show: venue_show.start_time > current_time, venue.shows)))
        })
    city_state['venues'] = venues_list
    data.append(city_state)
    print(data)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  current_time = datetime.now()
  search_term = request.form.get('search_term', '')
  response = {}
  venues = list(Venue.query.filter(Venue.name.ilike(f'%{search_term}%')| 
    Venue.state.ilike(f'%{search_term}%')| Venue.city.ilike(f'%{search_term}%')
    ).all()
  )
  response['count'] = len(venues)
  response['data'] = []
  for venue in venues:
    venue_dict = {
    'id': venue.id,
    'name':venue.name,
    'upcoming_shows': len(list(filter(lambda x: x.start_time > current_time, venue.shows)))
    }
    response['data'].append(venue_dict)
  print(response)
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue   page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  past_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  venue = Venue.query.get(venue_id)
 

  # past_shows_query = list(filter(lambda show: show.start_time < current_time, venue.shows))
  past_shows = []
  for past_show in past_shows_query:
    show ={
      "artist_id": past_show.artist.id,
      "artist_name": past_show.artist.name,
      'artist_genres': past_show.artist.genres.split(','),
      "artist_image_link": past_show.artist.image_link,
      "start_time": past_show.start_time.strftime('%m/%d/%y, %H:%M:%S')
      }
    past_shows.append(show)


  # Upcoming shows
  
  upcoming_shows = []
  for upcoming_show in upcoming_shows_query:
    show ={
      "artist_id": upcoming_show.artist.id,
      "artist_name": upcoming_show.artist.name,
      "artist_image_link": upcoming_show.artist.image_link,
      "start_time": upcoming_show.start_time.strftime('%m/%d/%y, %H:%M:%S')
      }
    upcoming_shows.append(show)
  
  
  venue.genres = venue.genres.split(',')
  venue.past_shows=  past_shows
  venue.past_shows_count= len(past_shows)
  print(venue.past_shows)
  venue.upcoming_shows= upcoming_shows
  venue.upcoming_shows_count=len(upcoming_shows)

  
  return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  try:
    form = VenueForm(request.form)
    if form.validate():
      venue = Venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        address = form.address.data,
        genres = ','.join(form.genres.data),
        facebook_link = form.facebook_link.data,
        image_link = form.image_link.data,
        website_link = form.website_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
        )
      db.session.add(venue)
      db.session.commit()

      # on successful db insert, flash success
      flash('Venue ' + request.form.data + ' was successfully listed!')
  # on successful db insert, flash success
  #flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    print(sys.exc_info())
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete')
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  venue = Venue.query.get(venue_id)
  try:
    db.session.delete(venue)
    db.session.commit()
    flash('Venue  was successfully removed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue  could not be removed checklog for error.')
    print(sys.exc_info())
  finally:
    db.session.close()


  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  data = []
  for artist in artists:
    artist_dict = {
    'id':artist.id,
    'name':artist.name
    }
    data.append(artist_dict)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  current_time = datetime.now()
  search_term = request.form.get('search_term', '')
  response = {}
  artists = list(Artist.query.filter(Artist.name.ilike(f'%{search_term}%')| 
    Artist.state.ilike(f'%{search_term}%')| Artist.city.ilike(f'%{search_term}%')
    ).all()
  )
  response['count'] = len(artists)
  response['data'] = []
  for artist in artists:
    artist_dict = {
    'id': artist.id,
    'name':artist.name,
    'upcoming_shows': len(list(filter(lambda x: x.start_time > current_time, artist.shows)))
    }
    response['data'].append(artist_dict)
  print(response)
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  # current_time = datetime.now()
  artist = Artist.query.get(artist_id)
  past_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  

 
  past_shows = []
  for past_show in past_shows_query:
    show ={
      "venue_id": past_show.venue.id,
      "venue_name": past_show.venue.name,
      "venue_image_link": past_show.venue.image_link,
      "venue_time": past_show.start_time.strftime('%m/%d/%y, %H:%M:%S')
      }
    past_shows.append(show)
  
  

  # Upcoming shows
  
  upcoming_shows = []
  for upcoming_show in upcoming_shows_query:
    show ={
      "venue_id": upcoming_show.venue.id,
      "venue_name": upcoming_show.venue.name,
      "venue_image_link": upcoming_show.venue.image_link,
      "start_time": upcoming_show.start_time.strftime('%m/%d/%y, %H:%M:%S')
      }
    upcoming_shows.append(show)
  # artist_dict = {
  #   'genres': artist.genres.split(','),
  #   'past_shows': past_shows,
  #   'past_shows_count': len(past_shows),
  #   'upcoming_shows': upcoming_shows,
  #   'upcoming_shows_count': len(upcoming_shows)

  # } 
  
  artist.genres = artist.genres.split(',')
  artist.past_shows=  past_shows
  artist.past_shows_count= len(past_shows)
  print(artist.past_shows)
  artist.upcoming_shows= upcoming_shows
  artist.upcoming_shows_count=len(upcoming_shows)
  print(artist) 
  # print(artist.upcoming_shows)
  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  #print (artist.name)
  form.genres.data = artist.genres.split(',')
  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website_link
  form.facebook_link.data = artist.facebook_link
 #form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description,
  form.image_link.data = artist.image_link

  #TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  if form.validate():
    try:
      artist = Artist.query.get(artist_id)
    
      artist.name = form.name.data,
      artist.city = form.city.data,
      artist.state = form.state.data,
      artist.phone = form.phone.data,
      artist.genres = ','.join(form.genres.data),
      artist.facebook_link = form.facebook_link.data,
      artist.image_link = form.image_link.data,
      artist.website_link = form.website_link.data,
      #rtist.seeking_venue = form.seeking_venue.data,
      artist.seeking_description = form.seeking_description.data
      db.session.add(artist)
      db.session.commit()
            # on successful dupdate, flash success
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
      db.session.rollback()
      flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')
      print(sys.exc_info())
    finally:
      db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  form.genres.data = venue.genres.split(',')
  form.name.data = venue.name,
  form.address.data=venue.address,
  form.city.data = venue.city,
  form.state.data =venue.state,
  form.phone.data = venue.phone,
  form.website_link.data =venue.website_link,
  form.facebook_link.data=venue.facebook_link,
  form.seeking_talent.data = venue.seeking_talent,
  form.seeking_description.data =venue.seeking_description,
  form.image_link.data=venue.image_link
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  if form.validate():
    try:
      venue = Venue.query.get(venue_id)
    
      venue.name = form.name.data,
      venue.city = form.city.data,
      venue.state = form.state.data,
      venue.phone = form.phone.data,
      venue.address = form.address.data,
      venue.genres = ','.join(form.genres.data),
      venue.facebook_link = form.facebook_link.data,
      venue.image_link = form.image_link.data,
      venue.website_link = form.website_link.data,
      venue.seeking_talent = form.seeking_talent.data,
      venue.seeking_description = form.seeking_description.data
      db.session.add(venue)
      db.session.commit()
            # on successful dupdate, flash success
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
    except:
      db.session.rollback()
      flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')
      print(sys.exc_info())
    finally:
      db.session.close()
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
  # TODO: modify data to be the data object returned from db insertion
  try:
    form = ArtistForm(request.form)
    if form.validate():
      artist = Artist(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        genres = ','.join(form.genres.data),
        facebook_link = form.facebook_link.data,
        image_link = form.image_link.data,
        website_link = form.website_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data
        )
      db.session.add(artist)
      db.session.commit()

      # on successful db insert, flash success
      flash('Artist ' + form.name.data + ' was successfully listed!')
  # on successful db insert, flash success
  #flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    print(sys.exc_info())
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  shows = Show.query.all()
  data = []
  for show in shows:
    show_dict = {
    "venue_id": show.venue.id,
    "venue_name": show.venue.name,
    "artist_id": show.artist.id,
    "artist_name": show.artist.name,
    "artist_image_link": show.artist.image_link,
    "start_time": show.start_time.strftime('%m/%d/%y, %H:%M:%S')
  }
    data.append(show_dict)
  
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
  try:
    form = ShowForm(request.form)
    if form.validate():
      show = Show(
        artist_id = form.artist_id.data,
        venue_id = form.venue_id.data,
        start_time = form.start_time.data)

      db.session.add(show)
      db.session.commit()

  # on successful db insert, flash success
    flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  except:
    db.session.rollback()
    flash('An error occurred. Show  could not be listed.')
    print(sys.exc.info())
  finally:
    db.session.close()
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
