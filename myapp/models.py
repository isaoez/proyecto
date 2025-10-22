from django.db import models
from django.contrib.auth.models import User

# El modelo para tus géneros y sub-géneros
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    padre = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategorias')

    def __str__(self):
        return self.nombre

# El artículo que el usuario OFRECE
class Articulo(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    propietario = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Aquí se asignan los géneros al artículo
    categorias = models.ManyToManyField(Categoria, related_name='articulos')

    def __str__(self):
        return self.titulo

# El deseo del usuario (lo que BUSCA a cambio de ese artículo)
class Deseo(models.Model):
    # El artículo al que está atado este deseo
    articulo_ofrecido = models.OneToOneField(Articulo, on_delete=models.CASCADE)
    
    # Aquí se asignan los géneros que busca
    categorias_buscadas = models.ManyToManyField(Categoria, related_name='deseos')

    def __str__(self):
        return 'Deseo para ' + self.articulo_ofrecido.titulo