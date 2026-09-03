from typing import ClassVar

from core.constants import RATING_SCORE_MAX, RATING_SCORE_MIN
from peewee import (
    Check,
    DateTimeField,
    FloatField,
    ForeignKeyField,
    IntegerField,
    TextField,
)
from playhouse.sqlite_ext import FTSModel, RowIDField, SearchField

from .database import BaseModel, db


class Album(BaseModel):
    title = TextField()
    artist = TextField()
    album_artist = TextField()
    release_year = IntegerField(null=True)
    cover_url = TextField(null=True)
    genres = TextField(null=True)
    rating_score = FloatField(null=True)
    rating_count = IntegerField(null=True)
    year_position = IntegerField(null=True)
    overall_position = IntegerField(null=True)
    url = TextField(null=True)
    last_rating_refresh = DateTimeField(null=True)


class AlbumIndex(FTSModel):
    rowid = RowIDField()
    title = SearchField()
    artist = SearchField()

    class Meta:
        database = db
        options: ClassVar[dict[str, str]] = {"tokenize": "porter"}


class Rating(BaseModel):
    user = TextField()
    score = IntegerField(
        constraints=[Check(f"score BETWEEN {RATING_SCORE_MIN} AND {RATING_SCORE_MAX}")]
    )
    album = ForeignKeyField(Album, backref="ratings")
    review = TextField(null=True)

    class Meta:
        indexes = ((("user", "album"), True),)


class UserInfo(BaseModel):
    user_id = TextField(unique=True)
    rym_username = TextField(null=True)
    lastfm_username = TextField(null=True)


class RatingHistory(BaseModel):
    album = ForeignKeyField(Album, backref="rating_histories")
    rating_score = FloatField()
    rating_count = IntegerField()
    timestamp = DateTimeField()

    class Meta:
        indexes = ((("album", "timestamp"), False),)
