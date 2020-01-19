from flask import jsonify

import api.http_errors as exceptions
from api.string_utilities import list_join

def error_response(error):
    data = {} if error.data == None else error.data
    response = jsonify(error=error.description, success=False, **data)
    response.status_code = error.code

    return response

def init_app(app):
    '''
    Registers all the error handlers to the specified application.
    '''

    usage: app.register_error_handler(exceptions.BadContentTypeError, error_response)
    usage: app.register_error_handler(exceptions.InvalidDataError, error_response)
    usage: app.register_error_handler(exceptions.AudioFileLoadError, error_response)