#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import dateutil.parser
import babel
from flask import (
    Flask, 
    render_template, 
    request, 
    flash, 
    redirect, 
    url_for
)
from flask_migrate import Migrate
from flask_moment import Moment
from datetime import datetime
import logging
from logging import Formatter, FileHandler
from forms import *
from models import db, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
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
    data_areas = []

    areas = Venue.query \
        .with_entities(Venue.city, Venue.state) \
        .group_by(Venue.city, Venue.state) \
        .all()
    
    for area in areas:
        data_venues = []

        venues = Venue.query \
            .filter_by(state=area.state) \
            .filter_by(city=area.city) \
            .all()
    
        for venue in venues:
            upcoming_shows = db.session \
                .query(Show) \
                .filter(Show.venue_id ==venue.id) \
                .filter(Show.start_time > datetime.now()) \
                .all()

            data_venues.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(upcoming_shows)
            })

        data_areas.append({
            'city': area.city,
            'state': area.state,
            'venues': data_venues
        })

    return render_template('pages/venues.html', areas=data_areas)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term')
    venues = Venue.query.filter(
        Venue.name.ilike('%{}%'.format(search_term))).all()

    data = []
    for venue in venues:
        tmp = {}
        tmp['id'] = venue.id
        tmp['name'] = venue.name
        tmp['num_upcoming_shows'] = len(venue.shows)
        data.append(tmp)

    response = {}
    response['count'] = len(data)
    response['data'] = data
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venue = Venue.query.get_or_404(venue_id)

    past_shows = []
    upcoming_shows = []

    for show in venue.shows:
        temp_show = {
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime('%m/%d/%Y, %H:%M')
        }
        if show.start_time <= datetime.now():
            past_shows.append(temp_show)
        else:
            upcoming_shows.append(temp_show)

    data = venue.to_dict()

    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)

    print(venue.to_dict())

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    error = False
    form = VenueForm(request.form)
    
    try:
        venue = Venue()
        form.populate_obj(venue)
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('An error occured. Venue ' + request.form['name'] + 'Could not be listed.')
        else:
            flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
    error = False
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash('Delete action could not be completed. Try again')
        else:
            flash('Venue sucessfully deleted')
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():

    data_artists = []

    artists = Artist.query.with_entities(Artist.id, Artist.name) \
        .order_by('id').all()

    for artist in artists:
        upcoming_shows = db.session \
            .query(Show) \
            .filter(Show.artist_id == artist.id) \
            .filter(Show.start_time > datetime.now()) \
            .all()
        
        data_artists.append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': len(upcoming_shows)
        })

    return render_template('pages/artists.html', artists=data_artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():

    search_term = request.form.get('search_term')
    artists = Artist.query.filter(
        Artist.name.ilike('%{}%'.format(search_term))).all()

    data_artists = []
    for artist in artists:
        upcoming_shows = db.session \
                .query(Show) \
                .filter(Show.artist_id == artist.id) \
                .filter(Show.start_time > datetime.now()) \
                .all()

        data_artists.append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': len(upcoming_shows)
        })

    response = {
        'data': data_artists,
        'count': len(artists)
    }

    return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.get_or_404(artist_id)

    past_shows = []
    upcoming_shows = []

    for show in artist.shows:
        temp_show = {
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime('%m %d %Y, %H:%M')
        }
        if show.start_time <= datetime.now():
            past_shows.append(temp_show)
        else:
            upcoming_shows.append(temp_show)

    data = artist.to_dict()

    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    artist = Artist.query.get(artist_id)
    form=ArtistForm(obj=artist)
    
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        error = False
        artist = Artist.query.get(artist_id)
        form = ArtistForm(request.form, meta={'csrf': False})

        if form.validate():
            artist.name = request.form['name']
            artist.city = request.form['city']
            artist.state = request.form['state']
            artist.phone = request.form['phone']
            tmp_genres = request.form.getlist('genres')
            artist.genres = ','.join(tmp_genres)
            artist.website_link = request.form['website_link']
            artist.image_link = request.form['image_link']
            artist.facebook_link = request.form['facebook_link']
            artist.seeking_description = request.form['seeking_description']
            db.session.add(artist)
            db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc.info())
    finally:
        db.session.close()
        if error:
            return redirect(url_for('server_error'))
        elif form.errors:
            return render_template('forms/edit_artist.html', form=form, artist=artist)
        else:
            return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)

    return render_template('forms/edit_venue.html', form=form, venue=venue.to_dict())

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        error = False
        venue = Venue.query.get(venue_id)
        form = VenueForm(request.form, meta={'csrf': False})
        if form.validate():
            venue.name = request.form['name']
            venue.city = request.form['city']
            venue.state = request.form['state']
            venue.address = request.form['address']
            venue.phone = request.form['phone']
            tmp_genres = request.form.getlist('genres')
            venue.genres = ','.join(tmp_genres)
            venue.image_link = request.form['image_link']
            venue.facebook_link = request.form['facebook_link']
            venue.website = request.form['website']
            venue.seeking_talent = True if 'seeking_talent' in request.form else False
            venue.seeking_description = request.form['seeking_description']
            db.session.add(venue)
            db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc.info())
    finally:
        db.session.close()
        if error:
            return redirect(url_for('server_error'))
        elif form.errors:
            return render_template('forms/edit_venue.html', form=form, venue=venue)
        else:
            return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    error = False
    form = ArtistForm(request.form)
    
    try:
        artist = Artist()
        form.populate_obj(artist)
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash ('An error occured. Artist ' + request.form['name'] + 'could not be added. Please try again.')
        else:
            flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = Show.query.all()

    data = []
    for show in shows:
        data.append({
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'artist_id': show.artist.id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.isoformat()
        })

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    form = ShowForm(request.form)

    try:
        show = Show()
        form.populate_obj(show)
        db.session.add(show)
        db.session.commit()  
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
        if error:
            flash ('Your show submission failed. Please try again.')
        else:
            flash('Show was successfully listed!')

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
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
