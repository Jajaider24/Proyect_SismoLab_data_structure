"""Reglas compartidas para calcular la prioridad de atencion de un nodo."""


def calculate_attention_priority(magnitude, depth_km, populated_zone):
    """Calcula prioridad 1, 2 o 3 desde magnitud, profundidad y zona.

    Args:
        magnitude: Magnitud sismica validada.
        depth_km: Profundidad del evento o nodo en kilometros.
        populated_zone: Indica si la ubicacion cae dentro de una zona poblada.

    Returns:
        int: Prioridad 3 para eventos criticos, 2 para magnitud media y 1
        para eventos de menor atencion.
    """
    if magnitude >= 6.0:
        return 3
    if magnitude >= 4.5:
        return 3 if depth_km <= 30.0 and populated_zone else 2
    return 1
