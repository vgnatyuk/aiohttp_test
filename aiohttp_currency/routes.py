from views import convert, database_merge


def setup_routes(app):
    app.router.add_get('/convert', convert)
    app.router.add_post('/database', database_merge)
