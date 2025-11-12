from django import forms
from .models import Categoria

# --- FORMULARIO 1: PARA CREAR PUBLICACIONES (CORREGIDO) ---

class PublicacionForm(forms.Form):
    
    # --- CAMPOS (Solo los de Artículo) ---
    titulo = forms.CharField(label='Título de tu artículo', max_length=200)
    descripcion = forms.CharField(label='Descripción', widget=forms.Textarea)
    imagen = forms.ImageField(label='Imagen del artículo', required=False)

    # --- CAMPOS DE CATEGORÍA ---
    
    # 1. El dropdown de categorías PADRE
    categoria_padre = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(padre=None),
        label="Categoría Principal",
        required=True, # Lo hacemos requerido
        empty_label="Selecciona una categoría principal"
    )
    
    # 2. Los checkboxes de subcategorías (se cargan con HTMX)
    #    Usamos 'initial' para que el form de EDICIÓN pueda pre-seleccionarlos
    categorias_ofrecidas = forms.ModelMultipleChoiceField(
        queryset=Categoria.objects.none(), # Se llena dinámicamente
        label='Subcategoría(s)',
        required=False, # No es requerido, la lógica la hacemos en clean()
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Lógica para cargar subcategorías si el formulario se carga con datos (ej. al editar)
        if 'initial' in kwargs and kwargs['initial'].get('categoria_padre'):
            padre_id = kwargs['initial']['categoria_padre']
            self.fields['categorias_ofrecidas'].queryset = Categoria.objects.filter(padre=padre_id)
        elif 'data' in args and args[0].get('categoria_padre'):
             padre_id = args[0].get('categoria_padre')
             self.fields['categorias_ofrecidas'].queryset = Categoria.objects.filter(padre=padre_id)


    # --- ¡LÓGICA DE VALIDACIÓN CORREGIDA! ---
    def clean(self):
        cleaned_data = super().clean()
        
        categorias_seleccionadas = cleaned_data.get('categorias_ofrecidas')
        padre = cleaned_data.get('categoria_padre')

        if not padre:
            # Si no seleccionó un padre (aunque es 'required', es una doble validación)
            self.add_error('categoria_padre', 'Debes seleccionar una categoría principal.')
            return cleaned_data

        if not categorias_seleccionadas:
            # --- AQUÍ ESTÁ EL ARREGLO ---
            # Caso 1: Se seleccionó un padre (ej: "Libros") Y este NO tiene hijos.
            if padre and not padre.subcategorias.exists():
                # ¡Correcto! El usuario quiere seleccionar "Libros".
                # Lo añadimos a la lista de categorías.
                cleaned_data['categorias_ofrecidas'] = [padre]
            
            # Caso 2: Se seleccionó un padre (ej: "Música") Y este SÍ tiene hijos.
            elif padre and padre.subcategorias.exists():
                # ... pero no se seleccionó ningún hijo (ej: "Rock"). Es un error.
                self.add_error('categorias_ofrecidas', 'Debes seleccionar al menos una subcategoría para la categoría padre elegida.')
        
        return cleaned_data


# --- FORMULARIO 2: PARA PREFERENCIAS (Sin cambios) ---

class PreferenciasForm(forms.Form):
    categorias_buscadas = forms.ModelMultipleChoiceField(
        label='Géneros que buscas',
        queryset=Categoria.objects.filter(subcategorias=None), # Solo categorías finales
        widget=forms.CheckboxSelectMultiple,
        required=False
    )