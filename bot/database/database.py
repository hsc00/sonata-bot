import os

from peewee import Model
from playhouse.sqlite_ext import SqliteExtDatabase

db_path = os.getenv("SONATA_BOT_DB_PATH", "sonata.db")
db = SqliteExtDatabase(
    db_path,
    pragmas=(
        ("journal_mode", "wal"),
        ("busy_timeout", 5000),
    ),
)


class BaseModel(Model):
    class Meta:
        database = db
