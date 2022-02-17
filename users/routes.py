from aiohttp import web

from . import views


routes = [
    web.post('/api/v1/registration/', views.registration),
    web.post('/api/v1/login/', views.login),
]
