from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('perfil/', views.ver_perfil, name='perfil'),
    path('mis-trueques/', views.ver_mis_trueques, name='mis_trueques'),
    path('oferta/nueva/<int:articulo_id>/', views.hacer_oferta, name='hacer_oferta'),
    path('ofertas-recibidas/', views.ver_ofertas_recibidas, name='ver_ofertas_recibidas'),
    path('oferta/aceptar/<int:oferta_id>/', views.aceptar_oferta, name='aceptar_oferta'),
    path('oferta/rechazar/<int:oferta_id>/', views.rechazar_oferta, name='rechazar_oferta'),
    path('ofertas-enviadas/', views.ver_ofertas_enviadas, name='ofertas_enviadas'),
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