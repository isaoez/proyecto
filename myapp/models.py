from django.db import models

# Create your models here.
class Project(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Task(models.Model):
    title = models.CharField(max_length=200) #solo texto
    description = models.TextField() #texto y numeros si no estoy mal
    project = models.ForeignKey(Project, on_delete=models.CASCADE) #uso de otra tabla
    done = models.BooleanField(default=False) #caracteristica que sirve para saber si esta hecha


    def __str__(self):
        return self.title + ' - ' + self.project.name