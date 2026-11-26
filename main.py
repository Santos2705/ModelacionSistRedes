import heapq


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
        if origen not in self.adyacencia:
            self.adyacencia[origen] = []
        if destino not in self.adyacencia:
            self.adyacencia[destino] = []

        self.adyacencia[origen].append((destino, tiempo_viaje, linea))

    def aplicar_retraso_linea(self, linea_afectada):
        """Duplica el tiempo de viaje de todos los túneles de la línea afectada."""
        for origen, vecinos in self.adyacencia.items():
            nuevos_vecinos = []
            for destino, tiempo_viaje, linea in vecinos:
                if linea == linea_afectada:
                    nuevos_vecinos.append((destino, tiempo_viaje * 2, linea))
                else:
                    nuevos_vecinos.append((destino, tiempo_viaje, linea))
            self.adyacencia[origen] = nuevos_vecinos

    def obtener_vecinos(self, estacion_id):
        return self.adyacencia.get(estacion_id, [])

    def obtener_tiempo_transbordo(self, estacion_id):
        return self.transbordos.get(estacion_id, 0)


def cargar_datos(ruta_archivo):
    grafo = GrafoMetro()
    lineas_validas = []

    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            linea_limpia = linea.strip()
            if linea_limpia and not linea_limpia.startswith("#"):
                lineas_validas.append(linea_limpia)

    indice = 0

    # 1. Número de estaciones y túneles
    num_estaciones, num_tuneles = map(int, lineas_validas[indice].split())
    indice += 1

    # 2. Estaciones y tiempos de transbordo
    for _ in range(num_estaciones):
        estacion_id, tiempo_transbordo = map(int, lineas_validas[indice].split())
        grafo.agregar_estacion(estacion_id, tiempo_transbordo)
        indice += 1

    # 3. Túneles dirigidos
    for _ in range(num_tuneles):
        partes = lineas_validas[indice].split()
        origen = int(partes[0])
        destino = int(partes[1])
        tiempo_viaje = int(partes[2])
        linea = partes[3]
        grafo.agregar_tunel(origen, destino, tiempo_viaje, linea)
        indice += 1

    # 4. Datos de la misión
    origen_pierre, origen_amelie, destino_pierre, destino_amelie = map(
        int, lineas_validas[indice].split()
    )
    indice += 1

    mision = {
        "origen_pierre": origen_pierre,
        "origen_amelie": origen_amelie,
        "destino_pierre": destino_pierre,
        "destino_amelie": destino_amelie,
    }

    # 5. Restricciones opcionales de líneas (Restricción 3)
    restricciones = {
        "retrasos": [],
        "sin_transbordo": [],  # lista de tuplas (linea, t_inicio, t_fin)
    }

    while indice < len(lineas_validas):
        partes = lineas_validas[indice].split()
        tipo = partes[0].upper()

        if tipo == "RETRASO" and len(partes) >= 2:
            linea_afectada = partes[1]
            restricciones["retrasos"].append(linea_afectada)
            grafo.aplicar_retraso_linea(linea_afectada)
        elif tipo == "SIN_TRANSBORDO" and len(partes) >= 4:
            linea_afectada = partes[1]
            t_inicio = int(partes[2])
            t_fin = int(partes[3])
            restricciones["sin_transbordo"].append((linea_afectada, t_inicio, t_fin))

        indice += 1

    return grafo, mision, restricciones


def construir_eventos(origen, movimientos, desfase=0):
    eventos = [{
        "tipo": "origen",
        "estacion": origen,
        "t_inicio": 0,
        "t_fin": desfase,
        "linea": "",
    }]
    reloj = desfase

    for est_ant, est_act, lin_ant, lin_act, t_trans, t_viaje in movimientos:
        if t_trans > 0:
            eventos.append({
                "tipo": "transbordo",
                "estacion": est_ant,
                "t_inicio": reloj,
                "t_fin": reloj + t_trans,
                "linea_origen": lin_ant,
                "linea": lin_act,
            })
            reloj += t_trans

        eventos.append({
            "tipo": "viaje",
            "origen": est_ant,
            "destino": est_act,
            "t_inicio": reloj,
            "t_fin": reloj + t_viaje,
            "linea": lin_act,
        })
        reloj += t_viaje

    return eventos


def k_rutas_con_transbordos(grafo, origen, destino, k=50):
    """
    Extensión de Dijkstra por estados (estacion, linea_actual) que obtiene
    hasta las k rutas simples más cortas ordenadas por tiempo total de viaje.
    """
    contador = 0
    # (tiempo_acumulado, contador, estacion, linea_actual, movimientos, visitados)
    cola = [(0, contador, origen, "", [], frozenset([origen]))]
    conteo_estados = {}
    rutas_encontradas = []

    while cola and len(rutas_encontradas) < k:
        tiempo_actual, _, estacion, linea_actual, movimientos, visitados = heapq.heappop(cola)

        estado = (estacion, linea_actual)
        conteo_estados[estado] = conteo_estados.get(estado, 0) + 1
        if conteo_estados[estado] > k:
            continue

        if estacion == destino:
            rutas_encontradas.append((tiempo_actual, movimientos))
            continue

        for vecino, tiempo_viaje, linea_nueva in grafo.obtener_vecinos(estacion):
            if vecino in visitados:
                continue

            if linea_actual != "" and linea_actual != linea_nueva:
                tiempo_transbordo = grafo.obtener_tiempo_transbordo(estacion)
            else:
                tiempo_transbordo = 0

            nuevo_tiempo = tiempo_actual + tiempo_transbordo + tiempo_viaje
            nuevos_movs = movimientos + [
                (estacion, vecino, linea_actual, linea_nueva, tiempo_transbordo, tiempo_viaje)
            ]
            contador += 1
            heapq.heappush(
                cola,
                (nuevo_tiempo, contador, vecino, linea_nueva, nuevos_movs, visitados | {vecino}),
            )

    return rutas_encontradas


def extraer_ocupaciones(eventos):
    """Extrae intervalos de ocupación de estaciones y túneles para verificar colisiones."""
    estaciones = []
    tuneles = []

    for ev in eventos:
        if ev["tipo"] == "origen":
            estaciones.append((ev["estacion"], ev["t_inicio"], ev["t_fin"]))
        elif ev["tipo"] == "transbordo":
            estaciones.append((ev["estacion"], ev["t_inicio"], ev["t_fin"]))
        elif ev["tipo"] == "viaje":
            tuneles.append((ev["origen"], ev["destino"], ev["t_inicio"], ev["t_fin"]))
            estaciones.append((ev["destino"], ev["t_fin"], ev["t_fin"]))

    return estaciones, tuneles


def hay_colision(eventos_p, eventos_a):
    est_p, tun_p = extraer_ocupaciones(eventos_p)
    est_a, tun_a = extraer_ocupaciones(eventos_a)

    # 1. No-colisión temporal en estaciones
    for e1, ini1, fin1 in est_p:
        for e2, ini2, fin2 in est_a:
            if e1 == e2 and max(ini1, ini2) <= min(fin1, fin2):
                return True

    # 2. No-colisión espacial en túneles (mismo sentido o sentido opuesto)
    for u1, v1, ini1, fin1 in tun_p:
        for u2, v2, ini2, fin2 in tun_a:
            mismo_tunel = (u1 == u2 and v1 == v2) or (u1 == v2 and v1 == u2)
            if mismo_tunel and max(ini1, ini2) < min(fin1, fin2):
                return True

    return False


def viola_sin_transbordo(eventos, restricciones_sin_transbordo):
    """Verifica si algún transbordo ocurre en una línea y horario prohibido."""
    if not restricciones_sin_transbordo:
        return False

    for ev in eventos:
        if ev["tipo"] == "transbordo":
            for linea_bloq, r_ini, r_fin in restricciones_sin_transbordo:
                if ev["linea_origen"] == linea_bloq or ev["linea"] == linea_bloq:
                    # Hay violación si el intervalo del transbordo se solapa con la ventana bloqueada
                    if ev["t_inicio"] < r_fin and ev["t_fin"] > r_ini:
                        return True
    return False


def planificar_escape(grafo, mision, restricciones, k=50):
    rutas_p = k_rutas_con_transbordos(
        grafo, mision["origen_pierre"], mision["destino_pierre"], k
    )
    rutas_a = k_rutas_con_transbordos(
        grafo, mision["origen_amelie"], mision["destino_amelie"], k
    )

    if not rutas_p or not rutas_a:
        return None

    # Ordenar combinaciones por T_max mínimo (desempate por suma de tiempos)
    candidatos = []
    for t_p, movs_p in rutas_p:
        for t_a, movs_a in rutas_a:
            t_max = max(t_p, t_a)
            candidatos.append((t_max, t_p + t_a, t_p, movs_p, t_a, movs_a))

    candidatos.sort(key=lambda x: (x[0], x[1]))

    sin_transbordo = restricciones.get("sin_transbordo", [])

    for t_max, _, t_p, movs_p, t_a, movs_a in candidatos:
        desfase_p = t_max - t_p
        desfase_a = t_max - t_a

        eventos_p = construir_eventos(mision["origen_pierre"], movs_p, desfase_p)
        eventos_a = construir_eventos(mision["origen_amelie"], movs_a, desfase_a)

        if viola_sin_transbordo(eventos_p, sin_transbordo):
            continue
        if viola_sin_transbordo(eventos_a, sin_transbordo):
            continue

        if not hay_colision(eventos_p, eventos_a):
            return {
                "t_max": t_max,
                "t_pierre": t_p,
                "t_amelie": t_a,
                "desfase_pierre": desfase_p,
                "desfase_amelie": desfase_a,
                "eventos_pierre": eventos_p,
                "eventos_amelie": eventos_a,
            }

    return None


def formatear_ruta(eventos, compuerta_etiqueta, desfase):
    lineas = []
    ultimo_indice = len(eventos) - 1

    for i, ev in enumerate(eventos):
        if ev["tipo"] == "origen":
            if desfase > 0:
                lineas.append(f"Minuto {ev['t_fin']}: Estación {ev['estacion']} (Origen - Inicia Movimiento)")
            else:
                lineas.append(f"Minuto {ev['t_inicio']}: Estación {ev['estacion']} (Origen)")
        elif ev["tipo"] == "transbordo":
            lineas.append(f"Minuto {ev['t_fin']}: Estación {ev['estacion']} (Termina Transbordo a {ev['linea']})")
        elif ev["tipo"] == "viaje":
            if i == ultimo_indice:
                lineas.append(f"Minuto {ev['t_fin']}: Estación {ev['destino']} (Destino Compuerta {compuerta_etiqueta})")
            else:
                lineas.append(f"Minuto {ev['t_fin']}: Estación {ev['destino']} (Viaje {ev['linea']})")

    return lineas


def generar_reporte(plan, ruta_salida="output.txt"):
    if plan is None:
        texto = (
            "=== PLAN DE ESCAPE CONFIGURADO ===\n"
            "Resultado de Sincronización: FALLO. No se encontró una ruta sincronizada sin colisiones.\n"
        )
    else:
        lineas = [
            "=== PLAN DE ESCAPE CONFIGURADO ===",
            f"Tiempo Total de la Operación: {plan['t_max']} minutos",
            "",
            "[PROGRAMACIÓN DE SALIDAS]",
        ]

        if plan["desfase_pierre"] > 0:
            lineas.append(
                f"Pierre arranca en el minuto: {plan['desfase_pierre']} "
                f"(Debe esperar {plan['desfase_pierre']} minutos en su estación de origen)"
            )
        else:
            lineas.append("Pierre arranca en el minuto: 0")

        if plan["desfase_amelie"] > 0:
            lineas.append(
                f"Amélie arranca en el minuto: {plan['desfase_amelie']} "
                f"(Debe esperar {plan['desfase_amelie']} minutos en su estación de origen)"
            )
        else:
            lineas.append("Amélie arranca en el minuto: 0")

        lineas.append("")
        lineas.append(f"[RUTA DE PIERRE (Tiempo total de viaje: {plan['t_pierre']} min)]")
        lineas.extend(formatear_ruta(plan["eventos_pierre"], "D1", plan["desfase_pierre"]))

        lineas.append("")
        lineas.append(f"[RUTA DE AMÉLIE (Tiempo total de viaje: {plan['t_amelie']} min)]")
        lineas.extend(formatear_ruta(plan["eventos_amelie"], "D2", plan["desfase_amelie"]))

        lineas.append("")
        lineas.append(
            f"Resultado de Sincronización: ÉXITO. Llegada simultánea en el minuto {plan['t_max']}."
        )

        texto = "\n".join(lineas) + "\n"

    with open(ruta_salida, "w", encoding="utf-8") as archivo:
        archivo.write(texto)

    print(texto)


if __name__ == "__main__":
    grafo, mision, restricciones = cargar_datos("input.txt")
    plan = planificar_escape(grafo, mision, restricciones)
    generar_reporte(plan, "output.txt")