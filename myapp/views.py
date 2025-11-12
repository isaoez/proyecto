from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import PublicacionForm, PreferenciasForm
from .models import Articulo, Deseo, Categoria 
from django.db.models import Q
# Create your views here.


def index(request):
    title = 'Últimas Publicaciones'
    
    # --- LÓGICA DE MATCHMAKING ---
    if request.user.is_authenticated:
        try:
            # 1. Obtenemos las categorías que el usuario desea
            categorias_deseadas = request.user.deseo.categorias_buscadas.all()
        except Deseo.DoesNotExist:
            categorias_deseadas = Categoria.objects.none()

        if categorias_deseadas.exists():
            # 2. Buscamos artículos que:
            #    - Pertenezcan a las categorías que el usuario desea (categorias__in)
            #    - Y NO sean propiedad del usuario actual (exclude propietario)
            articulos_filtrados = Articulo.objects.filter(
                categorias__in=categorias_deseadas
            ).exclude(
                propietario=request.user
            ).distinct() # .distinct() evita duplicados
            
            title = 'Coincidencias para ti'
        else:
            # 3. Si el usuario no tiene preferencias, mostramos todo (excepto lo suyo)
            articulos_filtrados = Articulo.objects.exclude(propietario=request.user)
            title = 'Todas las Publicaciones'
            
        articulos = articulos_filtrados.order_by('-id') # Mostramos los más nuevos primero

    else:
        # 4. Si el usuario no está logueado, mostramos todo
        articulos = Articulo.objects.all().order_by('-id')
    # --- FIN DE LA LÓGICA ---
    
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

    if articulo.propietario != request.user:
        return HttpResponseForbidden("No tienes permiso para editar este artículo.")

    if request.method == 'POST':
        # Al enviar datos, el formulario usa la lógica __init__ y clean que acabamos de arreglar
        form = PublicacionForm(request.POST, request.FILES)
        
        if form.is_valid():
            
            # 1. Actualiza el objeto Articulo
            articulo.titulo = form.cleaned_data['titulo']
            articulo.descripcion = form.cleaned_data['descripcion']
            
            if form.cleaned_data['imagen']:
                articulo.imagen = form.cleaned_data['imagen']
            
            # 2. ¡IMPORTANTE! Asignamos las categorías validadas por clean()
            articulo.categorias.set(form.cleaned_data['categorias_ofrecidas'])
            articulo.save()
            
            return redirect('perfil') # Redirigimos al perfil
    else:
        # --- LÓGICA GET (Cargar la página) ---
        
        # 1. Obtenemos la primera categoría guardada (o None)
        categoria_actual = articulo.categorias.first()
        
        if categoria_actual:
            # 2. Averiguamos si esta categoría es un "padre" o un "hijo"
            if categoria_actual.padre is None:
                # Es un padre (ej: "Libros")
                padre = categoria_actual
                subcategorias_marcadas = [] # Ninguna, porque el padre es la categoría final
            else:
                # Es un hijo (ej: "Rock")
                padre = categoria_actual.padre
                # Marcamos todos los "hermanos" que también estén guardados
                subcategorias_marcadas = articulo.categorias.filter(padre=padre)
        else:
            # El artículo no tiene categoría
            padre = None
            subcategorias_marcadas = []

        # 3. Pasamos los datos iniciales al formulario
        datos_iniciales = {
            'titulo': articulo.titulo,
            'descripcion': articulo.descripcion,
            'categoria_padre': padre,
            'categorias_ofrecidas': subcategorias_marcadas
        }
        form = PublicacionForm(initial=datos_iniciales)

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
    # Obtenemos el objeto Deseo del usuario (o lo creamos si no existe)
    deseo, created = Deseo.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        form = PreferenciasForm(request.POST) # Se lee el POST
        if form.is_valid():
            # 'set' reemplaza todas las categorías por las seleccionadas
            deseo.categorias_buscadas.set(form.cleaned_data['categorias_buscadas'])
            deseo.save()
            
            # ¡ARREGLO DE REDIRECCIÓN!
            return redirect('perfil') 
    else:
        # GET: Mostramos el formulario con las preferencias actuales
        form = PreferenciasForm(initial={
            'categorias_buscadas': deseo.categorias_buscadas.all()
        })

    return render(request, 'editar_preferencias.html', {'form': form})
@login_required
def ver_perfil(request):
    mis_articulos = Articulo.objects.filter(propietario=request.user).order_by('-id')
    contexto = {
        'mis_articulos': mis_articulos
    }
    return render(request, 'perfil.html', contexto)

@login_required
def ver_mis_trueques(request):
    # Buscamos todos los trueques sugeridos donde participa el usuario
    trueques_sugeridos = request.user.trueques_sugeridos.filter(estado='SUGERIDO')

    return render(request, 'mis_trueques.html', {
        'trueques_sugeridos': trueques_sugeridos
    })