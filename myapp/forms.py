from django import forms
from .models import Categoria, Articulo, Oferta 

class PublicacionForm(forms.Form):
    
    titulo = forms.CharField(label='Título de tu artículo', max_length=200)
    descripcion = forms.CharField(label='Descripción', widget=forms.Textarea)
    imagen = forms.ImageField(label='Imagen del artículo', required=False)
    
    categoria_padre = forms.ModelChoiceField(
        label='Género Principal (Ofrecido)',
        queryset=Categoria.objects.filter(padre=None).order_by('nombre'),
        required=True, 
        empty_label="Selecciona una categoría principal"
    )
    
    categorias_ofrecidas = forms.ModelMultipleChoiceField(
        queryset=Categoria.objects.all(),
        label='Subgéneros (Ofrecidos)',
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        padre_id = None
        
        if 'data' in args or 'data' in kwargs:
            data = args[0] if 'data' in args else kwargs['data']
            try:
                padre_id = int(data.get('categoria_padre'))
            except (ValueError, TypeError):
                padre_id = None
        
        elif 'initial' in kwargs and kwargs['initial'].get('categoria_padre'):
            try:
                padre_obj = kwargs['initial']['categoria_padre']
                padre_id = padre_obj.id
            except (AttributeError, ValueError, TypeError):
                padre_id = None

        if padre_id:
            try:
                padre_obj = Categoria.objects.get(id=padre_id)
                if padre_obj.subcategorias.exists():
                    opciones_visibles = Categoria.objects.filter(padre_id=padre_id).order_by('nombre').values_list('id', 'nombre')
                    self.fields['categorias_ofrecidas'].choices = opciones_visibles
                else:
                    self.fields['categorias_ofrecidas'].choices = []
            
            except Categoria.DoesNotExist:
                self.fields['categorias_ofrecidas'].choices = []
        else:
            self.fields['categorias_ofrecidas'].choices = []

    def clean(self):
        cleaned_data = super().clean()
        
        categorias_seleccionadas = cleaned_data.get('categorias_ofrecidas')
        padre = cleaned_data.get('categoria_padre')

        if not padre:
            return cleaned_data 

        if not categorias_seleccionadas:
            if padre.subcategorias.exists() == False:
                cleaned_data['categorias_ofrecidas'] = [padre]
            else:
                self.add_error('categorias_ofrecidas', 'Debes seleccionar al menos una subcategoría para la categoría padre elegida.')
        
        elif padre and categorias_seleccionadas:
             for cat in categorias_seleccionadas:
                if cat.padre != padre:
                    self.add_error('categorias_ofrecidas', f"La subcategoría '{cat.nombre}' no pertenece a '{padre.nombre}'.")
                    break 
        
        return cleaned_data

class PreferenciasForm(forms.Form):
    categorias_buscadas = forms.ModelMultipleChoiceField(
        label='Géneros que buscas',
        queryset=Categoria.objects.filter(subcategorias__isnull=True).order_by('nombre'),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

class OfertaForm(forms.ModelForm):
    class Meta:
        model = Oferta
        fields = ['articulo_ofrecido']
        labels = {
            'articulo_ofrecido': 'Selecciona el artículo que quieres ofrecer a cambio'
        }

    def __init__(self, *args, **kwargs):
        usuario_ofertante = kwargs.pop('usuario', None) 
        super().__init__(*args, **kwargs)
        
        if usuario_ofertante:
            self.fields['articulo_ofrecido'].queryset = Articulo.objects.filter(propietario=usuario_ofertante)
        
        self.fields['articulo_ofrecido'].widget.attrs.update({'class': 'form-control'})