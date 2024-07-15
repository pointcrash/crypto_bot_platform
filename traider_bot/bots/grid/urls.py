from django.urls import path

from bots.grid.views import grid_bot_create, grid_bot_edit

urlpatterns = [
    path('create', grid_bot_create, name='grid_bot_create'),
    path('edit/<int:bot_id>', grid_bot_edit, name='grid_bot_edit'),

]