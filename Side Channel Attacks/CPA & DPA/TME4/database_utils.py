from peewee import Model, CharField, BlobField, SqliteDatabase, DatabaseProxy
import struct

KEY_LEN = 16

database = DatabaseProxy()

class Trace(Model):
    key = CharField(max_length=KEY_LEN)
    textin = CharField(max_length=KEY_LEN)
    wave = BlobField()

    class Meta:
        database = database

class Database:
    def __init__(self, file='traces.db'):
        self.db = SqliteDatabase(file)
        database.initialize(self.db)

    def fill_db(self, traces, nb_samples):
        self.db.create_tables([Trace])
        for wave, textin, _, key in traces:
            trace = Trace.create(
                    key    = key.hex(),
                    textin = textin.hex(),
                    wave   = struct.pack('d' * nb_samples, *wave))
            trace.save()
