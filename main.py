class GrafoMetro:
    def __init__(self):
        # {estacion_id: tiempo_transbordo}
        self.transbordos = {}
        # Lista de adyacencia: {origen: [(destino, tiempo_viaje, linea), ...]}
        self.adyacencia = {}

    def agregar_estacion(self, estacion_id, tiempo_transbordo):
        self.transbordos[estacion_id] = tiempo_transbordo
        if estacion_id not in self.adyacencia:
            self.adyacencia[estacion_id] = []

    def agregar_tunel(self, origen, destino, tiempo_viaje, linea):
        # Aseguramos que los nodos existan en la lista de adyacencia
        if origen not in self.adyacencia:
            self.adyacencia[origen] = []
        if destino not in self.adyacencia:
            self.adyacencia[destino] = []
        
        self.adyacencia[origen].append((destino, tiempo_viaje, linea))

    def obtener_vecinos(self, estacion_id):
        return self.adyacencia.get(estacion_id, [])

    def obtener_tiempo_transbordo(self, estacion_id):
        return self.transbordos.get(estacion_id, 0)

    def mostrar_grafo(self):
        print("=== RED DEL METRO CARGADA ===")
        for estacion, vecinos in sorted(self.adyacencia.items()):
            t_transbordo = self.obtener_tiempo_transbordo(estacion)
            print(f"Estación {estacion} (Transbordo: {t_transbordo} min) -> {vecinos}")


def cargar_datos(ruta_archivo):
    grafo = GrafoMetro()
    lineas_validas = []

    # 1. Leer archivo ignorando comentarios (#) y líneas en blanco
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            linea_limpia = linea.strip()
            if linea_limpia and not linea_limpia.startswith("#"):
                lineas_validas.append(linea_limpia)

    indice = 0

    # 2. Leer cantidad de estaciones y túneles
    num_estaciones, num_tuneles = map(int, lineas_validas[indice].split())
    indice += 1

    # 3. Leer estaciones y sus tiempos de transbordo
    for _ in range(num_estaciones):
        estacion_id, tiempo_transbordo = map(int, lineas_validas[indice].split())
        grafo.agregar_estacion(estacion_id, tiempo_transbordo)
        indice += 1

    # 4. Leer túneles dirigidos (aristas)
    for _ in range(num_tuneles):
        partes = lineas_validas[indice].split()
        origen = int(partes[0])
        destino = int(partes[1])
        tiempo_viaje = int(partes[2])
        linea = partes[3]
        grafo.agregar_tunel(origen, destino, tiempo_viaje, linea)
        indice += 1

    # 5. Leer datos de la misión
    origen_pierre, origen_amelie, destino_pierre, destino_amelie = map(
        int, lineas_validas[indice].split()
    )

    mision = {
        "origen_pierre": origen_pierre,
        "origen_amelie": origen_amelie,
        "destino_pierre": destino_pierre,
        "destino_amelie": destino_amelie,
    }

    return grafo, mision


if __name__ == "__main__":
    grafo, mision = cargar_datos("input.txt")
    grafo.mostrar_grafo()
    print("\n=== DATOS DE LA MISIÓN ===")
    print(f"Pierre: Estación {mision['origen_pierre']} -> Compuerta {mision['destino_pierre']}")
    print(f"Amélie: Estación {mision['origen_amelie']} -> Compuerta {mision['destino_amelie']}")