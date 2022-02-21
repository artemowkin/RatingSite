from aiohttp import web

from . import views


routes = [
    web.post('/api/v1/registration/', views.registration),
    web.post('/api/v1/login/', views.login),
    web.get('/api/v1/users/', views.all_users),
    web.post('/api/v1/friends/add/', views.add_friend),
    web.get('/api/v1/friends/{user_id}/', views.get_user_friends),
    web.get('/api/v1/users/current/', views.current_user_info),
    web.get('/api/v1/users/{user_id}/', views.another_user_info),
]
