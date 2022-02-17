from aiohttp.web import json_response
from psycopg2.errors import UniqueViolation

from .services import RegistrationService, LoginService


async def registration(request):
    auth_data = await request.json()
    async with request.app['db'].acquire() as conn:
        service = RegistrationService()
        try:
            response = await service.registrate_user(conn, auth_data)
        except UniqueViolation:
            return json_response({'error': 'User already exists'}, status=400)

    status = 200 if 'jwt_token' in response else 400
    return json_response(response, status=status)


async def login(request):
    auth_data = await request.json()
    async with request.app['db'].acquire() as conn:
        service = LoginService()
        response = await service.login_user(conn, auth_data)

    status = 200 if 'jwt_token' in response else 400
    return json_response(response, status=status)
