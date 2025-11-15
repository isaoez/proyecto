# myapp/management/commands/encontrar_trueques.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Articulo, Deseo, Categoria, TruequeSugerido
from collections import defaultdict
from django.db import transaction

class Command(BaseCommand):
    help = 'Encuentra ciclos de trueque (cadenas) basados en artículos específicos'

    def handle(self, *args, **options):
        self.stdout.write("Borrando sugerencias antiguas...")
        # Usamos una transacción para asegurar que todo se haga de una vez
        with transaction.atomic():
            # Borramos las sugerencias que aún están pendientes
            TruequeSugerido.objects.filter(estado='SUGERIDO').delete()

            self.stdout.write("Construyendo grafo de artículos...")
            # 1. Construir el grafo de "qué artículo quiere qué artículo"
            grafo = self.construir_grafo()
            
            self.stdout.write("Buscando ciclos...")
            # 2. Encontrar todos los ciclos en el grafo (basado en Artículos)
            todos_los_ciclos = self.encontrar_ciclos(grafo)
            
            self.stdout.write(f"Se encontraron {len(todos_los_ciclos)} ciclos. Guardando...")
            # 3. Guardar los ciclos válidos en la base de datos
            self.guardar_ciclos(todos_los_ciclos)
        
        self.stdout.write("¡Búsqueda completada!")

    def construir_grafo(self):
        # grafo = { articulo_id_A: [lista_de_articulo_id_B] }
        # Donde A quiere lo que B tiene
        grafo = defaultdict(list)
        
        # Obtenemos todos los artículos y sus propietarios y preferencias
        # Esto optimiza mucho la consulta
        articulos = Articulo.objects.select_related('propietario__deseo').prefetch_related('propietario__deseo__categorias_buscadas').all()
        
        for articulo_a in articulos:
            propietario_a = articulo_a.propietario
            try:
                # Obtenemos las categorías que desea el propietario de A
                categorias_deseadas_por_a = propietario_a.deseo.categorias_buscadas.all()
            except Deseo.DoesNotExist:
                continue
                
            if not categorias_deseadas_por_a:
                continue
            
            # Buscamos todos los artículos (B) que:
            # 1. Pertenezcan a las categorías que A desea
            # 2. NO pertenezcan al propietario de A
            articulos_b_compatibles = Articulo.objects.filter(
                categorias__in=categorias_deseadas_por_a
            ).exclude(
                propietario=propietario_a
            )
            
            # Añadimos una "flecha" desde el artículo A hacia todos los artículos B compatibles
            grafo[articulo_a.id].extend([b.id for b in articulos_b_compatibles])
            
        return grafo

    def encontrar_ciclos(self, grafo):
        nodos = list(grafo.keys())
        todos_los_ciclos = []
        
        for nodo_inicial_id in nodos:
            stack_dfs = [(nodo_inicial_id, [nodo_inicial_id])] # (nodo_actual, [camino_hasta_ahora])
            
            while stack_dfs:
                nodo_actual_id, camino = stack_dfs.pop()
                
                for vecino_id in grafo.get(nodo_actual_id, []):
                    if vecino_id == nodo_inicial_id:
                        # ¡CICLO ENCONTRADO! (Ej: 1 -> 5 -> 9 -> 1)
                        if len(camino) >= 2: # Mínimo 2 artículos
                            todos_los_ciclos.append(tuple(camino))
                    elif vecino_id not in camino:
                        if len(camino) < 5: # Límite de 5 artículos por cadena
                            nuevo_camino = camino + [vecino_id]
                            stack_dfs.append((vecino_id, nuevo_camino))
                                
        # Devolvemos solo los ciclos únicos (usamos sorted para normalizar, ej: [1,5] y [5,1])
        ciclos_unicos = set(tuple(sorted(c)) for c in todos_los_ciclos)
        return list(ciclos_unicos)

    def guardar_ciclos(self, ciclos):
        for ciclo_ids in ciclos:
            articulos_en_ciclo = list(Articulo.objects.filter(id__in=ciclo_ids).select_related('propietario'))
            
            # Verificación de seguridad: ¿todos los artículos tienen dueños diferentes?
            propietarios_ids = set(art.propietario_id for art in articulos_en_ciclo)
            if len(propietarios_ids) != len(articulos_en_ciclo):
                # Esto es un "auto-ciclo" (ej. A quiere B, B quiere C, C quiere A, pero A y C son el mismo usuario).
                # Lo saltamos.
                continue

            # Creamos el trueque y añadimos los participantes
            trueque = TruequeSugerido.objects.create(estado='SUGERIDO')
            trueque.participantes.set(User.objects.filter(id__in=propietarios_ids))
            
            # --- ¡NUEVO! Construimos el JSON con la cadena exacta ---
            detalles = []
            
            # Necesitamos re-ordenar los artículos para que sigan el flujo del ciclo
            # Esta es una forma simple de hacerlo para 2 o 3 artículos
            # (Una implementación más robusta usaría el 'camino' original del DFS)
            
            if len(articulos_en_ciclo) == 2:
                art_A = articulos_en_ciclo[0]
                art_B = articulos_en_ciclo[1]
                detalles.append({"de_usuario_id": art_A.propietario_id, "articulo_id": art_A.id, "para_usuario_id": art_B.propietario_id})
                detalles.append({"de_usuario_id": art_B.propietario_id, "articulo_id": art_B.id, "para_usuario_id": art_A.propietario_id})

            # (Aquí se añadiría la lógica para len(articulos_en_ciclo) == 3, etc.)
            # Por ahora, nos centramos en la de 2
            
            if detalles:
                trueque.detalles_cadena = detalles
                trueque.save()
            else:
                # Si no pudimos armar los detalles, borramos el trueque
                trueque.delete()