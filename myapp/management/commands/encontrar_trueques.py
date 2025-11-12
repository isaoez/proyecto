# myapp/management/commands/encontrar_trueques.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Articulo, Deseo, Categoria, TruequeSugerido
from collections import defaultdict

class Command(BaseCommand):
    help = 'Encuentra ciclos de trueque (cadenas) en la base de datos'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando búsqueda de trueques...")

        # 1. Construir el grafo de "quién quiere qué"
        #    (Esto se basa en categorías, no en artículos específicos)
        grafo = self.construir_grafo()

        # 2. Encontrar todos los ciclos en el grafo
        #    Usaremos un algoritmo de Búsqueda en Profundidad (DFS)
        todos_los_ciclos = self.encontrar_ciclos(grafo)

        # 3. Guardar los ciclos válidos en la base de datos
        self.guardar_ciclos(todos_los_ciclos)

        self.stdout.write(f"¡Búsqueda completada! Se encontraron {len(todos_los_ciclos)} ciclos.")

    def construir_grafo(self):
        # grafo = { user_id: [lista_de_ids_de_usuarios_que_tienen_lo_que_quiere] }
        grafo = defaultdict(list)
        usuarios = User.objects.all().prefetch_related('deseo__categorias_buscadas')

        for usuario_a in usuarios:
            try:
                categorias_deseadas = usuario_a.deseo.categorias_buscadas.all()
            except Deseo.DoesNotExist:
                continue

            if not categorias_deseadas:
                continue

            # Buscamos artículos que coincidan con las categorías deseadas
            # y que no sean del propio usuario
            articulos_coincidentes = Articulo.objects.filter(
                categorias__in=categorias_deseadas
            ).exclude(propietario=usuario_a).values_list('propietario_id', flat=True).distinct()

            grafo[usuario_a.id].extend(list(articulos_coincidentes))

        return grafo

    def encontrar_ciclos(self, grafo):
        nodos = list(grafo.keys())
        todos_los_ciclos = []

        for nodo_inicial in nodos:
            # stack_dfs = [(nodo_actual, [camino_hasta_ahora])]
            stack_dfs = [(nodo_inicial, [nodo_inicial])]

            while stack_dfs:
                nodo_actual, camino = stack_dfs.pop()

                for vecino in grafo.get(nodo_actual, []):
                    if vecino == nodo_inicial:
                        # ¡CICLO ENCONTRADO! (Ej: A -> B -> A)
                        if len(camino) >= 2: # Mínimo 2 usuarios
                            todos_los_ciclos.append(tuple(sorted(camino)))
                    elif vecino not in camino:
                        if len(camino) < 5: # Límite de 5 usuarios por cadena
                            nuevo_camino = camino + [vecino]
                            stack_dfs.append((vecino, nuevo_camino))

        # Devolvemos solo los ciclos únicos
        return list(set(todos_los_ciclos))

    def guardar_ciclos(self, ciclos):
        # Borramos las sugerencias antiguas
        TruequeSugerido.objects.filter(estado='SUGERIDO').delete()

        for ciclo_ids in ciclos:
            # Creamos el nuevo trueque sugerido
            trueque = TruequeSugerido.objects.create(estado='SUGERIDO')

            # Añadimos a los participantes
            participantes = User.objects.filter(id__in=ciclo_ids)
            trueque.participantes.set(participantes)