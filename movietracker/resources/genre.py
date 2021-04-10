import json
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import validate, ValidationError
from sqlalchemy.exc import IntegrityError
from movietracker import db
from movietracker.models import Genre, Movie, Series
from movietracker.constants import *
from movietracker.utils import MovieTrackerBuilder, create_error_response, get_uuid

class GenreCollection(Resource):
    
    def get(self):
        body = MovieTrackerBuilder()
        body.add_namespace("mt", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.genrecollection"))
        body.add_control_all_movies()
        body.add_control_all_series()
        body["items"] = []

        for db_genre in Genre.query.all():
            item = MovieTrackerBuilder(
                name=db_genre.name
            )
            item.add_control("self", url_for("api.genreitem", genre=db_genre.name))
            item.add_control("profile", GENRE_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)


class GenreItem(Resource):

    def get(self, genre):
        db_genre = Genre.query.filter_by(name=genre).first()

        if db_genre is None:
            return create_error_response(404,
                "Genre not found",
                "Genre with name '{}' does not exist".format(genre)
            )

        body = MovieTrackerBuilder(
            name=db_genre.name
        )
        body.add_namespace("mt", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.genreitem", genre=db_genre.name))
        body.add_control("up", url_for("api.genrecollection"))
        body.add_control_movies_by_genre(db_genre.name)
        body.add_control_series_by_genre(db_genre.name)

        return Response(json.dumps(body), 200, mimetype=MASON)


class MoviesByGenreCollection(Resource):

    def get(self, genre):
        db_genre = Genre.query.filter_by(name=genre).first()

        if db_genre is None:
            return create_error_response(404,
                "Genre not found",
                "Genre with name '{}' does not exist".format(genre)
            )
        
        body = MovieTrackerBuilder(
            name=db_genre.name
        )
        body.add_control("self", url_for("api.moviesbygenrecollection", genre=db_genre.name))
        body.add_control("up", url_for("api.genreitem", genre=db_genre.name))
        body.add_control_add_movie(db_genre.name, Movie.get_schema_post())
        body["items"] = []
        
        for db_movie in db_genre.movies:
            item = MovieTrackerBuilder(
                title=db_movie.title,
                actors=db_movie.actors,
                release_date=db_movie.release_date,
                score=db_movie.score
            )
            item.add_control("self", url_for("api.movieitem", movie=db_movie.uuid))
            item.add_control("profile", MOVIE_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self, genre):
        db_genre = Genre.query.filter_by(name=genre).first()
        if db_genre is None:
            return create_error_response(404,
                "Genre not found",
                "Genre with name '{}' does not exist".format(genre)
            )

        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Movie.get_schema_post())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        # set uuid and genre for the new movie entry
        movie = Movie(
            uuid=get_uuid(),
            genre=db_genre
        )

        # set everything else for the new movie entry
        for i in request.json:
            setattr(movie, i, request.json[i])

        db.session.add(movie)
        db.session.commit()
        
        return Response(status=201, headers={
                "Location": url_for("api.movieitem", movie=movie.uuid)
            }, mimetype=MASON
            )


class SeriesByGenreCollection(Resource):

    def get(self, genre):
        db_genre = Genre.query.filter_by(name=genre).first()

        if db_genre is None:
            return create_error_response(404,
                "Genre not found",
                "Genre with name '{}' does not exist".format(genre)
            )
        
        body = MovieTrackerBuilder(
            name=db_genre.name
        )
        body.add_control("self", url_for("api.seriesbygenrecollection", genre=db_genre.name))
        body.add_control("up", url_for("api.genreitem", genre=db_genre.name))
        body.add_control_add_series(db_genre.name, Series.get_schema_post())
        body["items"] = []
        
        for db_series in db_genre.series:
            item = MovieTrackerBuilder(
                title=db_series.title,
                actors=db_series.actors,
                release_date=db_series.release_date,
                score=db_series.score,
                seasons=db_series.seasons
            )
            item.add_control("self", url_for("api.seriesitem", series=db_series.uuid))
            item.add_control("profile", SERIES_PROFILE)
            body["items"].append(item)
            
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self, genre):
        db_genre = Genre.query.filter_by(name=genre).first()

        if db_genre is None:
            return create_error_response(404,
                "Not found",
                "Genre with name '{}' does not exist".format(genre)
            )

        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Series.get_schema_post())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        # set uuid and genre for the new series entry
        series = Series(
            uuid=get_uuid(),
            genre=db_genre
        )

        # set everything else for the new movie entry
        for i in request.json:
            setattr(series, i, request.json[i])

        db.session.add(series)
        db.session.commit()
    
        return Response(status=201, headers={
            "Location": url_for("api.seriesitem", series=series.uuid)
            }, mimetype=MASON
            )