from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('hello/<str:username>', views.hello, name='hello'),
    path('publicar/', views.crear_publicacion, name='publicar'),
    path('publicacion/<int:articulo_id>/editar/', views.editar_publicacion, name='editar_publicacion'),
    path('publicacion/<int:articulo_id>/eliminar/', views.eliminar_publicacion, name='eliminar_publicacion'),
    path('preferencias/', views.editar_preferencias, name='editar_preferencias'),
    path('login/', auth_views.LoginView.as_view(), name='login'),# URL para el Login
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),# URL para el Logout
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('signup/', views.signup, name='signup'),
    path('ajax/load-subcategorias/', views.load_subcategorias, name='ajax_load_subcategorias'),
]