from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('hello/<str:username>', views.hello, name='hello'),
    path('login/', auth_views.LoginView.as_view(), name='login'),# URL para el Login
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),# URL para el Logout
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('signup/', views.signup, name='signup'),
]
