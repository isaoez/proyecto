from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import PublicacionForm, PreferenciasForm
from .models import Articulo, Deseo, Categoria 
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

# --- VISTA DE PUBLICACIÓN (SIMPLIFICADA) ---
@login_required
def crear_publicacion(request):
    if request.method == 'POST':
        form = PublicacionForm(request.POST, request.FILES) # Acepta archivos
        if form.is_valid():
            
            # 1. Crea el objeto Articulo
            articulo_nuevo = Articulo.objects.create(
                propietario=request.user,
                titulo=form.cleaned_data['titulo'],
                descripcion=form.cleaned_data['descripcion'],
                imagen=form.cleaned_data['imagen']
            )
            # 2. Asigna las categorías seleccionadas al artículo
            articulo_nuevo.categorias.set(form.cleaned_data['categorias_ofrecidas'])

            # --- ¡LÓGICA DE CREAR DESEO ELIMINADA! ---
            
            return redirect('index') # O a donde quieras
    else:
        form = PublicacionForm()

    return render(request, 'crear_publicacion.html', {'form': form})

# --- VISTA DE EDICIÓN (SIMPLIFICADA) ---
@login_required
def editar_publicacion(request, articulo_id):
    articulo = get_object_or_404(Articulo, id=articulo_id)
    # --- ¡Ya no necesitamos obtener el deseo! ---

    if articulo.propietario != request.user:
        return HttpResponseForbidden("No tienes permiso para editar este artículo.")

    if request.method == 'POST':
        form = PublicacionForm(request.POST, request.FILES) # El form ya no tiene campos de deseo
        if form.is_valid():
            
            # 1. Actualiza el objeto Articulo
            articulo.titulo = form.cleaned_data['titulo']
            articulo.descripcion = form.cleaned_data['descripcion']
            if form.cleaned_data['imagen']:
                articulo.imagen = form.cleaned_data['imagen']
            articulo.categorias.set(form.cleaned_data['categorias_ofrecidas'])
            articulo.save()

            # --- ¡LÓGICA DE ACTUALIZAR DESEO ELIMINADA! ---
            
            return redirect('index')
    else:
        # GET: Muestra el formulario con los datos existentes
        datos_iniciales = {
            'titulo': articulo.titulo,
            'descripcion': articulo.descripcion,
            # NOTA: Poblar los campos de categoría HTMX en la edición
            # requiere lógica adicional, pero el formulario base funcionará.
        }
        form = PublicacionForm(initial=datos_iniciales)

    # Renderiza la plantilla de edición
    return render(request, 'editar_publicacion.html', {'form': form, 'articulo': articulo})


@login_required
def eliminar_publicacion(request, articulo_id):
    articulo = get_object_or_404(Articulo, id=articulo_id)

    if articulo.propietario != request.user:
        return HttpResponseForbidden("No tienes permiso para eliminar este artículo.")

    if request.method == 'POST':
        articulo.delete()
        return redirect('index')
    
    return render(request, 'eliminar_publicacion.html', {'articulo': articulo})


# --- ¡NUEVA VISTA PARA HTMX! (Sin cambios) ---
@login_required 
def load_subcategorias(request):
    """
    Vista para cargar las subcategorías basadas en la categoría padre seleccionada.
    """
    
    # Busca el ID del padre usando los nombres del formulario
    padre_id = request.GET.get('categoria_padre') or request.GET.get('categoria_buscada_padre')
    
    # El 'field_name' nos dirá si estamos pidiendo 'categorias_ofrecidas' o 'categorias_buscadas'
    field_name = request.GET.get('field_name', 'categorias_ofrecidas') 
    
    try:
        subcategorias = Categoria.objects.filter(padre_id=int(padre_id)).order_by('nombre')
    except (ValueError, TypeError):
        subcategorias = Categoria.objects.none()

    return render(request, 'partials/subcategorias_checkboxes.html', {
        'subcategorias': subcategorias,
        'field_name': field_name
    })

@login_required
def editar_preferencias(request):
    # Obtenemos el objeto Deseo del usuario
    deseo, created = Deseo.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        form = PreferenciasForm(request.POST)
        if form.is_valid():
            # 'set' reemplaza todas las categorías por las seleccionadas
            deseo.categorias_buscadas.set(form.cleaned_data['categorias_buscadas'])
            deseo.save()
            return redirect('editar_preferencias')
    else:
        # --- Lógica de GET (mucho más simple) ---
        # Solo le decimos al formulario qué categorías están 
        # seleccionadas actualmente en el 'initial' data.
        form = PreferenciasForm(initial={
            'categorias_buscadas': deseo.categorias_buscadas.all()
        })

    return render(request, 'editar_preferencias.html', {'form': form})