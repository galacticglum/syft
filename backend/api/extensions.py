'''
Flask and other extensions are instantiated here.
To avoid circular dependencies, all extensions are housed in this module.
They are initialized in application.py.
'''

import click

from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate(db=db)

def init_app(app):
    '''
    Initializes all extensions using the specified Flask app context.
    :param app:
        The app context to use for extension initialization.
    '''

    db.init_app(app)
    migrate.init_app(app)

    app.cli.add_command(__init_db_command)

@click.command('init-db')
@with_appcontext
def __init_db_command():
    '''
    The 'init-db' shell command.
    
    '''

    confirmation = click.confirm('Are you sure you would like to continue? This will drop and recreate all tables in the database.')  
    if confirmation:
        db.create_all()
        click.echo('Initialized the database: dropped and recreated all tables.')