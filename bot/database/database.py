import os

from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase

db_path = os.getenv("SONATA_BOT_DB_PATH", "sonata.db")

# Ensure the directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

db = SqliteExtDatabase("sonata.db", pragmas=(("journal_mode", "wal"),))


class BaseModel(Model):
    class Meta:
        database = db
