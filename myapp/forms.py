from django import forms
from .models import Categoria

class PublicacionForm(forms.Form):
    
    # Campos para el ARTÍCULO (Lo que ofreces)
    titulo = forms.CharField(label='Título de tu artículo', max_length=200)
    descripcion = forms.CharField(label='Descripción', widget=forms.Textarea)
    
    # ¡AQUÍ ESTÁ LA MAGIA!
    # Trae todas las Categorías de la BD y las muestra como checkboxes
    categorias_ofrecidas = forms.ModelMultipleChoiceField(
        label='Géneros de tu artículo (Opciones)',
        queryset=Categoria.objects.all(),
        widget=forms.CheckboxSelectMultiple # Esto crea los checkboxes
    )

    # Campos para el DESEO (Lo que buscas)
    categorias_buscadas = forms.ModelMultipleChoiceField(
        label='Géneros que buscas (Opciones)',
        queryset=Categoria.objects.all(),
        widget=forms.CheckboxSelectMultiple # También como checkboxes
    )