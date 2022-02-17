from aiohttp_security.abc import AbstractAuthorizationPolicy

from .db import users


class IsAuthenticatedAuthorizationPolicy(AbstractAuthorizationPolicy):
    """Authorization policy to check is user authenticated"""

    async def permits(self, identity, permission, context=None):
        return True

    async def authorized_userid(identity):
        return True
