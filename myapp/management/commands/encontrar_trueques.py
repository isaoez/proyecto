from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Articulo, Deseo, TruequeSugerido
from collections import defaultdict
from django.db import transaction

class Command(BaseCommand):
    help = 'Encuentra ciclos de trueque (cadenas) basados en artículos específicos'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando búsqueda de trueques...")
        
        with transaction.atomic():
            # 1. Borramos sugerencias antiguas pendientes
            TruequeSugerido.objects.filter(estado='SUGERIDO').delete()

            # 2. Construimos el grafo
            grafo = self.construir_grafo()
            
            # 3. Buscamos los ciclos (Ahora devuelve tuplas ordenadas)
            ciclos = self.encontrar_ciclos(grafo)
            
            self.stdout.write(f"Se encontraron {len(ciclos)} ciclos posibles.")
            
            # 4. Guardamos los ciclos (Ahora soporta cualquier longitud)
            self.guardar_ciclos(ciclos)
        
        self.stdout.write("¡Proceso completado!")

    def construir_grafo(self):
        # Grafo: { articulo_A_id : [articulo_B_id, articulo_C_id] }
        # Significa: El dueño de A quiere B o quiere C.
        grafo = defaultdict(list)
        articulos = Articulo.objects.select_related('propietario__deseo').prefetch_related('propietario__deseo__categorias_buscadas').all()
        
        for art_origen in articulos:
            comprador = art_origen.propietario
            try:
                cats_deseadas = comprador.deseo.categorias_buscadas.all()
            except Deseo.DoesNotExist:
                continue
                
            if not cats_deseadas:
                continue
            
            # Buscamos artículos que coincidan con lo que el dueño de 'art_origen' quiere
            # y que NO sean suyos.
            matches = Articulo.objects.filter(
                categorias__in=cats_deseadas
            ).exclude(propietario=comprador)
            
            # Creamos las aristas: art_origen -> match
            for match in matches:
                grafo[art_origen.id].append(match.id)
                
        return grafo

    def encontrar_ciclos(self, grafo):
        # Usamos DFS para encontrar ciclos de longitud 2 a 5
        ciclos_encontrados = set()
        
        def get_canonical(path):
            # Rota el ciclo para que empiece con el ID más pequeño
            # Esto evita duplicados como (A,B,C) y (B,C,A)
            min_idx = path.index(min(path))
            return tuple(path[min_idx:] + path[:min_idx])

        nodos = list(grafo.keys())
        for nodo in nodos:
            stack = [(nodo, [nodo])]
            
            while stack:
                curr, path = stack.pop()
                
                # Exploramos vecinos
                for vecino in grafo.get(curr, []):
                    if vecino == path[0]:
                        # ¡Ciclo cerrado!
                        if len(path) >= 2:
                            ciclo_canonico = get_canonical(path)
                            ciclos_encontrados.add(ciclo_canonico)
                    elif vecino not in path:
                        # Seguimos buscando si no excedemos el límite (5)
                        if len(path) < 5:
                            stack.append((vecino, path + [vecino]))
                            
        return list(ciclos_encontrados)

    def guardar_ciclos(self, ciclos):
        # Cargamos todos los artículos involucrados en memoria para no hacer miles de queries
        all_ids = set()
        for c in ciclos:
            all_ids.update(c)
        
        articulos_map = {a.id: a for a in Articulo.objects.filter(id__in=all_ids).select_related('propietario')}
        
        for ciclo_ids in ciclos:
            # ciclo_ids es una tupla ordenada: (ID_A, ID_B, ID_C)
            # Significa: A quiere B, B quiere C, C quiere A.
            
            articulos_ciclo = []
            try:
                for aid in ciclo_ids:
                    articulos_ciclo.append(articulos_map[aid])
            except KeyError:
                continue # Algún artículo se borró mientras procesábamos
            
            # Validación: Todos los dueños deben ser diferentes
            owners = set(a.propietario_id for a in articulos_ciclo)
            if len(owners) != len(articulos_ciclo):
                continue # Hay un usuario repetido en la cadena, lo saltamos

            # --- CONSTRUCCIÓN DEL JSON (GENÉRICA PARA N USUARIOS) ---
            detalles = []
            
            # Recorremos el ciclo. 
            # Si el ciclo es [A, B, C], significa:
            # El dueño de A quiere B -> B se mueve al dueño de A.
            # El dueño de B quiere C -> C se mueve al dueño de B.
            # El dueño de C quiere A -> A se mueve al dueño de C.
            
            for i in range(len(articulos_ciclo)):
                art_receptor = articulos_ciclo[i]
                # El artículo que se mueve es el SIGUIENTE en la lista (o el primero si estamos al final)
                art_movido = articulos_ciclo[(i + 1) % len(articulos_ciclo)]
                
                detalles.append({
                    "articulo_id": art_movido.id,               # El objeto que se transfiere
                    "de_usuario_id": art_movido.propietario.id, # Quien lo da
                    "para_usuario_id": art_receptor.propietario.id # Quien lo recibe (porque él lo "quería")
                })

            # Guardar en BD
            trueque = TruequeSugerido.objects.create(
                estado='SUGERIDO',
                detalles_cadena=detalles
            )
            trueque.participantes.set(User.objects.filter(id__in=owners))