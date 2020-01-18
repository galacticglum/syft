'''
Defines the search-related API routes.

'''

from flask import Blueprint, jsonify, request, current_app

bp = Blueprint('search', __name__, url_prefix='/api/search')

@bp.route('/test')
def test():
    return 'Hello World'