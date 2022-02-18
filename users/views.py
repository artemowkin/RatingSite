from aiohttp.web import json_response, Response
from psycopg2.errors import UniqueViolation, ForeignKeyViolation

from .services import (
    RegistrationService, LoginService, get_all_users, add_user_friend,
    GetUserFriendsService
)


def user_required(func):

    def wrapper(request):
        if not request.user:
            return json_response({'error': 'Not authenticated'}, status=403)

        return func(request)

    return wrapper


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


async def all_users(request):
    async with request.app['db'].acquire() as conn:
        all_users = await get_all_users(conn, request.user)

    return json_response(all_users)


@user_required
async def add_friend(request):
    async with request.app['db'].acquire() as conn:
        try:
            await add_user_friend(conn, request)
        except UniqueViolation:
            return json_response(
                {'error': 'User already in friends'}, status=400
            )
        except ForeignKeyViolation:
            return json_response(
                {'error': "User with this ID doesn't exist"}, status=400
            )

    return Response(status=204)


async def get_user_friends(request):
    user_id = request.match_info['user_id']
    service = GetUserFriendsService()
    async with request.app['db'].acquire() as conn:
        try:
            user_friends = await service.get_friends(conn, user_id)
        except ForeignKeyViolation:
            return json_response(
                {'error': "User with this ID doesn't exist"}, status=400
            )

    return json_response(user_friends)
