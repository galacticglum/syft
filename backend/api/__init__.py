import os
from flask import Flask

def create_app(instance_config_filename='local_config.py'):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Load the instance configuration.
    app.config.from_pyfile(instance_config_filename, silent=True)
    
    # Load the default global config file.
    app.config.from_object('api.config')

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize all the extensions, models, and routes
    from api import extensions, models, routes, error_handlers

    extensions.init_app(app)
    routes.init_app(app)
    error_handlers.init_app(app)

    return app