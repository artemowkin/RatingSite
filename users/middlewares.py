from aiohttp import web
from aiohttp_security.api import IDENTITY_KEY


@web.middleware
async def authentication_middleware(request, handler):
    payload = await request.app[IDENTITY_KEY].identify(request)
    if payload:
        request.user = payload
    else:
        request.user = None

    return await handler(request)
