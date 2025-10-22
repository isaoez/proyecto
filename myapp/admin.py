from django.contrib import admin
from .models import Categoria, Articulo, Deseo

# Registra los modelos en el panel de admin
admin.site.register(Categoria)
admin.site.register(Articulo)
admin.site.register(Deseo)