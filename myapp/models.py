# myapp/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save # ¡Importante!
from django.dispatch import receiver # ¡Importante!

# El modelo para tus géneros y sub-géneros
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    padre = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategorias')

    def __str__(self):
        ruta_completa = [self.nombre]
        k = self.padre
        while k is not None:
            ruta_completa.insert(0, k.nombre)
            k = k.padre
        return ' - '.join(ruta_completa)

# El artículo que el usuario OFRECE
class Articulo(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    propietario = models.ForeignKey(User, on_delete=models.CASCADE)
    categorias = models.ManyToManyField(Categoria, related_name='articulos')

    def __str__(self):
        return self.titulo

# --- ¡MODELO MODIFICADO! ---
# Ahora representa las PREFERENCIAS GENERALES del usuario
class Deseo(models.Model):
    # ¡CAMBIO! Se vincula directamente al Usuario.
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='deseo')
    
    # Las categorías que busca
    categorias_buscadas = models.ManyToManyField(Categoria, related_name='deseos')

    def __str__(self):
        return 'Preferencias de ' + self.usuario.username

# --- ¡NUEVA FUNCIÓN AUTOMÁTICA! ---
@receiver(post_save, sender=User)
def crear_o_actualizar_deseo_usuario(sender, instance, created, **kwargs):
    """
    Esta función se ejecuta automáticamente CADA VEZ que un User se guarda.
    Si el usuario es NUEVO (created=True), le crea un objeto Deseo vacío.
    """
    if created:
        Deseo.objects.create(usuario=instance)
    # Para usuarios existentes, solo guarda el perfil (si ya existía)
    instance.deseo.save()