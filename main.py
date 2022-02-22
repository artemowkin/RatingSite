from aiohttp import web
from aiohttp.web_middlewares import normalize_path_middleware
from aiohttp_security import JWTIdentityPolicy, setup as setup_secure

from ratingsite.routes import setup_routes
from ratingsite.settings import config
from ratingsite.db import pg_context
from users.authorization import IsAuthenticatedAuthorizationPolicy
from users.middlewares import authentication_middleware


app = web.Application()
app.middlewares.extend([
    authentication_middleware, normalize_path_middleware()
])
id_policy = JWTIdentityPolicy(config['jwt_secret'])
setup_secure(app, id_policy, IsAuthenticatedAuthorizationPolicy())
app['config'] = config
setup_routes(app)
app.cleanup_ctx.append(pg_context)
web.run_app(app)
