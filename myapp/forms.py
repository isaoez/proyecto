# myapp/forms.py
from django import forms
from .models import Categoria

class PublicacionForm(forms.Form):
    
    # --- CAMPOS (Sin cambios) ---
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
    categoria_buscada_padre = forms.ModelChoiceField(
        label='Género Principal (Buscado)',
        queryset=Categoria.objects.filter(padre=None).order_by('nombre'),
        required=False,
        empty_label="Selecciona una categoría principal"
    )
    categorias_buscadas = forms.ModelMultipleChoiceField(
        label='Subgéneros (Buscados)',
        queryset=Categoria.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    # --- MÉTODO __init__ (ACTUALIZADO) ---
    def __init__(self, *args, **kwargs):
        """
        Esto se actualiza para prevenir el crash de validación.
        Poblamos el queryset no solo con los hijos del padre,
        sino también con cualquier valor que ya venga en el POST.
        La validación real se hará en el método clean().
        """
        super().__init__(*args, **kwargs)
        
        # 'data' solo existe en peticiones POST
        if 'data' in kwargs and kwargs['data']:
            data = kwargs['data']

            # --- Lógica para 'categorias_ofrecidas' ---
            qs_ofrecidas = Categoria.objects.none()
            try:
                padre_id = int(data.get('categoria_padre'))
                qs_ofrecidas = Categoria.objects.filter(padre_id=padre_id)
            except (ValueError, TypeError):
                pass  # No se seleccionó padre, el queryset base es none()

            # ¡EL ARREGLO!
            # Añadimos los IDs que se enviaron en el POST al queryset
            # para que la validación de campo no falle.
            submitted_ofrecidas = data.getlist('categorias_ofrecidas')
            if submitted_ofrecidas:
                qs_ofrecidas = qs_ofrecidas | Categoria.objects.filter(pk__in=submitted_ofrecidas)
            
            self.fields['categorias_ofrecidas'].queryset = qs_ofrecidas.distinct().order_by('nombre')

            # --- Lógica para 'categorias_buscadas' ---
            qs_buscadas = Categoria.objects.none()
            try:
                padre_buscado_id = int(data.get('categoria_buscada_padre'))
                qs_buscadas = Categoria.objects.filter(padre_id=padre_buscado_id)
            except (ValueError, TypeError):
                pass
            
            submitted_buscadas = data.getlist('categorias_buscadas')
            if submitted_buscadas:
                qs_buscadas = qs_buscadas | Categoria.objects.filter(pk__in=submitted_buscadas)
            
            self.fields['categorias_buscadas'].queryset = qs_buscadas.distinct().order_by('nombre')

    # --- MÉTODO clean (NUEVO) ---
    def clean(self):
        """
        Aquí validamos la lógica de negocio.
        Nos aseguramos de que las subcategorías enviadas 
        realmente pertenezcan al padre seleccionado.
        """
        cleaned_data = super().clean()
        
        padre_ofrecido = cleaned_data.get('categoria_padre')
        categorias_ofrecidas = cleaned_data.get('categorias_ofrecidas')
        
        # Caso 1: Hay subcategorías pero no hay padre (datos huérfanos)
        if not padre_ofrecido and categorias_ofrecidas:
            # Simplemente los borramos
            cleaned_data['categorias_ofrecidas'] = Categoria.objects.none()
        
        # Caso 2: Hay padre y subcategorías (validamos que coincidan)
        elif padre_ofrecido and categorias_ofrecidas:
            for cat in categorias_ofrecidas:
                if cat.padre != padre_ofrecido:
                    # Esto previene un envío malicioso
                    raise forms.ValidationError(
                        f"La subcategoría '{cat.nombre}' no pertenece a '{padre_ofrecido.nombre}'."
                    )
        
        # --- Repetimos para 'buscadas' ---
        
        padre_buscado = cleaned_data.get('categoria_buscada_padre')
        categorias_buscadas = cleaned_data.get('categorias_buscadas')
        
        if not padre_buscado and categorias_buscadas:
            cleaned_data['categorias_buscadas'] = Categoria.objects.none()
            
        elif padre_buscado and categorias_buscadas:
            for cat in categorias_buscadas:
                if cat.padre != padre_buscado:
                    raise forms.ValidationError(
                        f"La subcategoría '{cat.nombre}' no pertenece a '{padre_buscado.nombre}'."
                    )

        return cleaned_data