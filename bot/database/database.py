from peewee import *
from playhouse.sqlite_ext import SqliteExtDatabase

db = SqliteExtDatabase("sonata.db", pragmas=(("journal_mode", "wal"),))


class BaseModel(Model):
    class Meta:
        database = db

