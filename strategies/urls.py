from django.urls import path
from . import views

urlpatterns = [
    path('', views.strategies, name='strategies'),
    path('search/', views.search_company, name='search_company'),
    path('<str:ticker>/technical_analysis/', views.technical_analysis_view, name='technical_analysis'),
    path('news/', views.fetch_company_news_view, name='fetch_company_news'),
]
