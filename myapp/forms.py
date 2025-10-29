from django import forms
from .models import Categoria

class PublicacionForm(forms.Form):
    
    # Campos para el ARTÍCULO (Lo que ofreces)
    titulo = forms.CharField(label='Título de tu artículo', max_length=200)
    descripcion = forms.CharField(label='Descripción', widget=forms.Textarea)
    
    # --- Nuevos campos para CATEGORÍAS OFRECIDAS ---
    
    # CAMPO 1: Categorías Principales (Padre)
    # Muestra solo las categorías que NO tienen padre
    categoria_padre = forms.ModelChoiceField(
        label='Género Principal (Ofrecido)',
        queryset=Categoria.objects.filter(padre=None).order_by('nombre'),
        required=False,
        empty_label="Selecciona una categoría principal"
    )

    # CAMPO 2: Subcategorías (Hijo)
    # Este queryset se llenará dinámicamente con HTMX.
    # Empezará vacío.
    categorias_ofrecidas = forms.ModelMultipleChoiceField(
        label='Subgéneros (Ofrecidos)',
        queryset=Categoria.objects.none(), # Se llena dinámicamente
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    # --- Nuevos campos para CATEGORÍAS BUSCADAS ---
    
    categoria_buscada_padre = forms.ModelChoiceField(
        label='Género Principal (Buscado)',
        queryset=Categoria.objects.filter(padre=None).order_by('nombre'),
        required=False,
        empty_label="Selecciona una categoría principal"
    )

    categorias_buscadas = forms.ModelMultipleChoiceField(
        label='Subgéneros (Buscados)',
        queryset=Categoria.objects.none(), # Se llena dinámicamente
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    def __init__(self, *args, **kwargs):
        """
        Esto es crucial para la validación.
        Cuando el formulario se envía (POST), self.data contiene los IDs.
        Debemos actualizar el queryset de los campos de subcategorías
        ANTES de que la validación ocurra.
        """
        super().__init__(*args, **kwargs)
        
        # Lógica para 'categorias_ofrecidas'
        if 'categoria_padre' in self.data:
            try:
                padre_id = int(self.data.get('categoria_padre'))
                self.fields['categorias_ofrecidas'].queryset = Categoria.objects.filter(padre_id=padre_id).order_by('nombre')
            except (ValueError, TypeError):
                pass  # El usuario no seleccionó un padre
        
        # Lógica para 'categorias_buscadas'
        if 'categoria_buscada_padre' in self.data:
            try:
                padre_id = int(self.data.get('categoria_buscada_padre'))
                self.fields['categorias_buscadas'].queryset = Categoria.objects.filter(padre_id=padre_id).order_by('nombre')
            except (ValueError, TypeError):
                pass