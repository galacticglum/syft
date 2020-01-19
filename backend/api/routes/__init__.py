from api.routes import search

def init_app(app):
    app.register_blueprint(search.bp)