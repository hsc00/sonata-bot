import os

from models import Album
from peewee import SqliteDatabase, TextField
from playhouse.migrate import SqliteMigrator, migrate

db_path = os.getenv("SONATA_BOT_DB_PATH", "sonata.db")
db = SqliteDatabase(db_path)
migrator = SqliteMigrator(db)

migrations = [
    migrator.add_column(Album._meta.table_name, "album_artist", TextField(null=True)),
]

migrate(*migrations)
