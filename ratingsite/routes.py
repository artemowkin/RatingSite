from aiohttp_swagger import setup_swagger

from users.routes import setup_users_routes


def setup_routes(app):
    setup_users_routes(app)
    setup_swagger(app, swagger_url='/api/v1/doc')
