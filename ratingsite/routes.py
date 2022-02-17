from ratings.routes import routes as ratings_routes
from users.routes import routes as users_routes


def setup_routes(app):
    app.add_routes(ratings_routes + users_routes)
