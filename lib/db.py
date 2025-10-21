from peewee import PostgresqlDatabase, Model, CharField, BooleanField, BigIntegerField
import dotenv
import os

dotenv.load_dotenv()


db_name = os.getenv('POSTGRES_DB')
db_user = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')
db_host = os.getenv('POSTGRES_HOST')
db_port = int(os.getenv('POSTGRES_PORT'))

if not all([db_name, db_user, db_password, db_host, db_port]):
    raise ValueError("Database configuration environment variables are not fully set.")

db = PostgresqlDatabase(
    db_name,
    user=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
)


class User(Model):
    """Peewee model for bot users.

    Fields:
      - id: Discord user ID (Int, primary key)
      - username: user's Discord username
      - daily: whether daily reminders are enabled
      - weekly: whether weekly reminders are enabled
    """

    id = BigIntegerField(primary_key=True)
    username = CharField()
    daily = BooleanField(default=False)
    weekly = BooleanField(default=False)

    class Meta:
        database = db
        table_name = 'users'

def initialize_db():
    """Initialize the database and create tables if they don't exist."""
    db.connect()
    db.create_tables([User], safe=True)