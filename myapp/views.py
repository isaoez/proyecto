from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import PublicacionForm
from .models import Articulo, Deseo
# Create your views here.


def index(request):
    title = 'Página Principal'
    articulos = Articulo.objects.all() 
    return render(request, 'index.html', {
        'title': title,
        'articulos': articulos
    })


def about(request):
    username = 'isao'
    return render(request, 'about.html', {
        'username': username
    })


def hello(request, username):
    return HttpResponse('<h1>Hello %s<h1>' % username)

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index') # Redirige al inicio después del registro
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {
        'form': form
    })

def signin(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            # Log in the user
            user = form.get_user()
            login(request, user)
            return redirect('index') # Redirige al inicio después del login
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {
        'form': form
    })

def signout(request):
    logout(request)
    return redirect('index') # Redirige al inicio después del logout

# VISTA DE PUBLICACIÓN PROTEGIDA
@login_required
def crear_publicacion(request):
    if request.method == 'POST':
        form = PublicacionForm(request.POST)
        if form.is_valid():
            
            # 1. Crea el objeto Articulo
            articulo_nuevo = Articulo.objects.create(
                propietario=request.user,
                titulo=form.cleaned_data['titulo'],
                descripcion=form.cleaned_data['descripcion']
            )
            # 2. Asigna las categorías seleccionadas al artículo
            articulo_nuevo.categorias.set(form.cleaned_data['categorias_ofrecidas'])

            # 3. Crea el Deseo asociado
            deseo_nuevo = Deseo.objects.create(
                articulo_ofrecido=articulo_nuevo
            )
            # 4. Asigna las categorías seleccionadas al deseo
            deseo_nuevo.categorias_buscadas.set(form.cleaned_data['categorias_buscadas'])
            
            return redirect('index') # O a donde quieras
    else:
        form = PublicacionForm()

    return render(request, 'crear_publicacion.html', {'form': form})
@login_required
def editar_publicacion(request, articulo_id):
    articulo = get_object_or_404(Articulo, id=articulo_id)
    deseo = articulo.deseo # Obtenemos el deseo asociado

    # ¡LA SEGURIDAD! Comprueba si el usuario es el dueño
    if articulo.propietario != request.user:
        return HttpResponseForbidden("No tienes permiso para editar este artículo.")

    if request.method == 'POST':
        form = PublicacionForm(request.POST)
        if form.is_valid():
            
            # 1. Actualiza el objeto Articulo
            articulo.titulo = form.cleaned_data['titulo']
            articulo.descripcion = form.cleaned_data['descripcion']
            articulo.categorias.set(form.cleaned_data['categorias_ofrecidas'])
            articulo.save() # Guarda los cambios del artículo

            # 2. Actualiza el Deseo asociado
            deseo.categorias_buscadas.set(form.cleaned_data['categorias_buscadas'])
            deseo.save() # Guarda los cambios del deseo
            
            return redirect('index') # Redirige al inicio
    else:
        # GET: Muestra el formulario con los datos existentes
        datos_iniciales = {
            'titulo': articulo.titulo,
            'descripcion': articulo.descripcion,
            'categorias_ofrecidas': articulo.categorias.all(),
            'categorias_buscadas': deseo.categorias_buscadas.all()
        }
        form = PublicacionForm(initial=datos_iniciales)

    return render(request, 'editar_publicacion.html', {'form': form, 'articulo': articulo})


@login_required
def eliminar_publicacion(request, articulo_id):
    articulo = get_object_or_404(Articulo, id=articulo_id)

    # ¡LA SEGURIDAD! Comprueba si el usuario es el dueño
    if articulo.propietario != request.user:
        return HttpResponseForbidden("No tienes permiso para eliminar este artículo.")

    if request.method == 'POST':
        # Si el usuario confirma (envió el form POST), borra
        articulo.delete()
        return redirect('index')
    
    # GET: Muestra la página de confirmación
    return render(request, 'eliminar_publicacion.html', {'articulo': articulo})