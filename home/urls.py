from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('ticker/<str:ticker>/', views.home, name='display_ticker'),

]