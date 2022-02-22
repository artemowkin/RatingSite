from aiohttp import web

from . import views


def setup_users_routes(app):
    app.router.add_view('/api/v1/registration/', views.RegistrationView)
    app.router.add_view('/api/v1/login/', views.LoginView)
    app.add_routes([
        web.get('/api/v1/users/', views.all_users),
        web.post('/api/v1/friends/add/', views.add_friend),
        web.get('/api/v1/friends/{user_nickname}/', views.get_user_friends),
        web.get('/api/v1/users/current/', views.current_user_info),
        web.get('/api/v1/users/search/{search_by}/', views.search_users),
        web.get('/api/v1/users/{user_nickname}/', views.another_user_info),
    ])
