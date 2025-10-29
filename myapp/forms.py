# myapp/forms.py
from django import forms
from .models import Categoria

# --- FORMULARIO 1: PARA CREAR PUBLICACIONES (YA SIMPLIFICADO) ---

class PublicacionForm(forms.Form):
    
    # --- CAMPOS (Solo los de Artículo) ---
    titulo = forms.CharField(label='Título de tu artículo', max_length=200)
    descripcion = forms.CharField(label='Descripción', widget=forms.Textarea)
    
    categoria_padre = forms.ModelChoiceField(
        label='Género Principal (Ofrecido)',
        queryset=Categoria.objects.filter(padre=None).order_by('nombre'),
        required=False,
        empty_label="Selecciona una categoría principal"
    )
    categorias_ofrecidas = forms.ModelMultipleChoiceField(
        label='Subgéneros (Ofrecidos)',
        queryset=Categoria.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    # --- MÉTODO __init__ (Simplificado) ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 
        
        if self.is_bound and self.data:
            data = self.data 

            # --- Lógica solo para 'categorias_ofrecidas' ---
            qs_ofrecidas = Categoria.objects.none()
            try:
                padre_id = int(data.get('categoria_padre'))
                qs_ofrecidas = Categoria.objects.filter(padre_id=padre_id)
            except (ValueError, TypeError):
                pass 

            submitted_ofrecidas = data.getlist('categorias_ofrecidas')
            if submitted_ofrecidas:
                qs_ofrecidas = qs_ofrecidas | Categoria.objects.filter(pk__in=submitted_ofrecidas)
            
            self.fields['categorias_ofrecidas'].queryset = qs_ofrecidas.distinct().order_by('nombre')

    # --- MÉTODO clean (Simplificado) ---
    def clean(self):
        cleaned_data = super().clean()
        
        padre_ofrecido = cleaned_data.get('categoria_padre')
        categorias_ofrecidas = cleaned_data.get('categorias_ofrecidas')
        
        if not padre_ofrecido and categorias_ofrecidas:
            cleaned_data['categorias_ofrecidas'] = Categoria.objects.none()
        
        elif padre_ofrecido and categorias_ofrecidas:
            for cat in categorias_ofrecidas:
                if cat.padre != padre_ofrecido:
                    raise forms.ValidationError(
                        f"La subcategoría '{cat.nombre}' no pertenece a '{padre_ofrecido.nombre}'."
                    )
        
        return cleaned_data

# --- FORMULARIO 2: PARA EDITAR PREFERENCIAS (NUEVO) ---

class PreferenciasForm(forms.Form):
    """
    Formulario simplificado para editar preferencias.
    Ahora muestra TODAS las categorías en un solo campo.
    """
    
    categorias_buscadas = forms.ModelMultipleChoiceField(
        label='Géneros que buscas',
        
        # --- ¡ESTE ES EL ÚNICO CAMBIO! ---
        # En lugar de .all(), filtramos por las categorías
        # que NO tienen subcategorías (son "hojas" del árbol).
        # El related_name 'subcategorias' viene de tu models.py
        queryset=Categoria.objects.filter(subcategorias__isnull=True).order_by('nombre'),
        # --- FIN DEL CAMBIO ---
        
        widget=forms.CheckboxSelectMultiple,
        required=False
    )