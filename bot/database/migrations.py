import os

from peewee import DateTimeField, SqliteDatabase, TextField
from playhouse.migrate import SqliteMigrator

from .models import Album, Artist

db_path = os.getenv("SONATA_BOT_DB_PATH", "sonata.db")
db = SqliteDatabase(db_path)
migrator = SqliteMigrator(db)


def get_pending_migrations() -> list:
    album_exists = db.table_exists(Album._meta.table_name)  # noqa: SLF001
    artist_exists = db.table_exists(Artist._meta.table_name)  # noqa: SLF001

    album_columns = (
        {column.name for column in db.get_columns(Album._meta.table_name)}  # noqa: SLF001
        if album_exists
        else set()
    )
    artist_columns = (
        {column.name for column in db.get_columns(Artist._meta.table_name)}  # noqa: SLF001
        if artist_exists
        else set()
    )

    migrations = [
        migrator.add_column(
            Album._meta.table_name,  # noqa: SLF001
            "album_artist",
            TextField(null=True),
        ),
        migrator.add_column(
            Album._meta.table_name,  # noqa: SLF001
            "last_rating_refresh",
            DateTimeField(null=True),
        ),
        migrator.add_column(
            Artist._meta.table_name,  # noqa: SLF001
            "last_influences_refresh",
            DateTimeField(null=True),
        ),
    ]

    pending = []
    for operation, column, table_exists, columns in zip(
        migrations,
        ["album_artist", "last_rating_refresh", "last_influences_refresh"],
        [album_exists, album_exists, artist_exists],
        [album_columns, album_columns, artist_columns],
    ):
        if table_exists and column not in columns:
            pending.append(operation)

    return pending
