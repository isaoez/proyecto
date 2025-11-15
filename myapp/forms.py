# myapp/forms.py
from django import forms
# ¡CAMBIO! Añadimos Articulo y Oferta
from .models import Categoria, Articulo, Oferta 

# --- FORMULARIO 1: PARA CREAR PUBLICACIONES (CORREGIDO) ---

class PublicacionForm(forms.Form):
    
    # --- CAMPOS ---
    titulo = forms.CharField(label='Título de tu artículo', max_length=200)
    descripcion = forms.CharField(label='Descripción', widget=forms.Textarea)
    imagen = forms.ImageField(label='Imagen del artículo', required=False)
    
    categoria_padre = forms.ModelChoiceField(
        label='Género Principal (Ofrecido)',
        queryset=Categoria.objects.filter(padre=None).order_by('nombre'),
        # ¡CAMBIO! Lo hacemos requerido
        required=True, 
        empty_label="Selecciona una categoría principal"
    )
    categorias_ofrecidas = forms.ModelMultipleChoiceField(
        queryset=Categoria.objects.none(), # Se llena dinámicamente
        label='Subgéneros (Ofrecidos)',
        required=False, # La lógica 'required' la hacemos en clean()
        widget=forms.CheckboxSelectMultiple
    )
    
    # --- ¡MÉTODO __init__ CORREGIDO! ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        data = None
        # Comprobamos si estamos en un POST (con datos) o GET (con initial)
        if 'data' in args:
            data = args[0]
        elif 'data' in kwargs:
            data = kwargs['data']

        # --- Lógica para POST (al enviar el formulario) ---
        if data:
            try:
                padre_id = int(data.get('categoria_padre'))
                # Seteamos el queryset a los hijos de ese padre
                qs_hijos = Categoria.objects.filter(padre_id=padre_id).order_by('nombre')
                self.fields['categorias_ofrecidas'].queryset = qs_hijos
            except (ValueError, TypeError):
                self.fields['categorias_ofrecidas'].queryset = Categoria.objects.none()
        
        # --- Lógica para GET (al cargar la página de "Editar") ---
        elif 'initial' in kwargs and kwargs['initial'].get('categoria_padre'):
            try:
                padre_id = kwargs['initial']['categoria_padre']
                self.fields['categorias_ofrecidas'].queryset = Categoria.objects.filter(padre=padre_id).order_by('nombre')
            except (ValueError, TypeError):
                 self.fields['categorias_ofrecidas'].queryset = Categoria.objects.none()

    # --- ¡MÉTODO clean CORREGIDO! ---
    def clean(self):
        cleaned_data = super().clean()
        
        categorias_seleccionadas = cleaned_data.get('categorias_ofrecidas')
        padre = cleaned_data.get('categoria_padre')

        if not padre:
            # El campo ya es 'required', así que Django lo validará primero
            return cleaned_data 

        if not categorias_seleccionadas:
            # Caso 1: Se seleccionó un padre (ej: "Libros") Y este NO tiene hijos.
            if padre.subcategorias.exists() == False:
                # ¡Correcto! El usuario quiere seleccionar "Libros".
                cleaned_data['categorias_ofrecidas'] = [padre]
            
            # Caso 2: Se seleccionó un padre (ej: "Música") Y este SÍ tiene hijos.
            else:
                # ... pero no se seleccionó ningún hijo (ej: "Rock"). Es un error.
                self.add_error('categorias_ofrecidas', 'Debes seleccionar al menos una subcategoría para la categoría padre elegida.')
        
        elif padre and categorias_seleccionadas:
             # Caso 3: Verificamos que las subcategorías pertenezcan al padre.
             for cat in categorias_seleccionadas:
                if cat.padre != padre:
                    self.add_error('categorias_ofrecidas', f"La subcategoría '{cat.nombre}' no pertenece a '{padre.nombre}'.")
                    break 
        
        return cleaned_data

# --- FORMULARIO 2: PARA PREFERENCIAS (Sin cambios) ---

class PreferenciasForm(forms.Form):
    categorias_buscadas = forms.ModelMultipleChoiceField(
        label='Géneros que buscas',
        queryset=Categoria.objects.filter(subcategorias__isnull=True).order_by('nombre'),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )


# --- ¡AQUÍ ESTÁ EL FORMULARIO QUE FALTABA! ---
class OfertaForm(forms.ModelForm):
    class Meta:
        model = Oferta
        fields = ['articulo_ofrecido'] # El usuario solo necesita elegir esto
        labels = {
            'articulo_ofrecido': 'Selecciona el artículo que quieres ofrecer a cambio'
        }

    def __init__(self, *args, **kwargs):
        # Sacamos el 'usuario' que le pasaremos desde la vista
        usuario_ofertante = kwargs.pop('usuario', None) 
        super().__init__(*args, **kwargs)
        
        if usuario_ofertante:
            # Filtramos el QuerySet para mostrar SOLO los artículos del ofertante
            self.fields['articulo_ofrecido'].queryset = Articulo.objects.filter(propietario=usuario_ofertante)
        
        # Opcional: añadimos una clase para que se vea bien
        self.fields['articulo_ofrecido'].widget.attrs.update({'class': 'form-control'})