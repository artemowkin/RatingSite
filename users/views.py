from aiohttp.web import json_response, Response, View
from psycopg2.errors import UniqueViolation, ForeignKeyViolation
from pydantic import ValidationError

from .services import (
    RegistrationService, LoginService, get_all_users, add_user_friend,
    GetUserFriendsService, get_user_info, GetAnotherUserInfoService,
    SearchUsersService
)
from .serializers import RegistrationData, LoginData


def user_required(func):

    def wrapper(request):
        if not request.user:
            return json_response({'error': 'Not authenticated'}, status=403)

        return func(request)

    return wrapper


class RegistrationView(View):

    async def _get_auth_data(self):
        request_body = await self.request.text()
        auth_data = RegistrationData.parse_raw(request_body)
        return auth_data

    async def _registrate_user(self, auth_data):
        async with self.request.app['db'].acquire() as conn:
            service = RegistrationService(conn)
            response = await service.registrate_user(auth_data)
            return response

    async def post(self):
        try:
            auth_data = await self._get_auth_data()
            response = await self._registrate_user(auth_data)
            return json_response(response)
        except ValidationError as e:
            return json_response(e.json(), status=400)
        except UniqueViolation:
            return json_response({'error': 'User already exists'}, status=400)


class LoginView(View):

    async def _get_auth_data(self):
        request_body = await self.request.text()
        auth_data = LoginData.parse_raw(request_body)
        return auth_data

    async def _login_user(self, auth_data):
        async with self.request.app['db'].acquire() as conn:
            service = LoginService(conn)
            response = await service.login_user(auth_data)
            return response

    async def post(self):
        try:
            auth_data = await self._get_auth_data()
            response = await self._login_user(auth_data)
            status = 200 if 'jwt_token' in response else 400
            return json_response(response, status=status)
        except ValidationError as e:
            return json_response(e.json(), status=400)


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
    user_nickname = request.match_info['user_nickname']
    async with request.app['db'].acquire() as conn:
        try:
            service = GetUserFriendsService(conn)
            user_friends = await service.get_friends_by_nick(user_nickname)
        except ForeignKeyViolation:
            return json_response({
                'error': "User with this ID doesn't exist"
            }, status=400)
        except IndexError:
            return json_response({
                'error': 'There is no user with this nickname'
            }, status=400)

    return json_response(user_friends)


@user_required
async def current_user_info(request):
    async with request.app['db'].acquire() as conn:
        user_info = await get_user_info(conn, request.user['nickname'])

    return json_response(user_info)


async def another_user_info(request):
    current_user_id = request.user['id'] if request.user else None
    another_user_nickname = request.match_info['user_nickname']
    async with request.app['db'].acquire() as conn:
        info_service = GetAnotherUserInfoService(conn, current_user_id)
        try:
            user_info = await info_service.get_info(another_user_nickname)
        except IndexError:
            return json_response({
                'error': 'There is no user with this nickname'
            }, status=400)

    return json_response(user_info)


async def search_users(request):
    current_user_id = request.user['id'] if request.user else None
    search_by = request.match_info['search_by']
    async with request.app['db'].acquire() as conn:
        search_service = SearchUsersService(conn, current_user_id)
        users = await search_service.search(search_by)
        return json_response(users)
