from .db_singleton import DatabaseSingleton

def obtener_disponibles():
    db = DatabaseSingleton()
    query = """
        SELECT l.id_lote, l.especie, l.peso_disponible_kg, l.precio_kg,
               u.nombre AS proveedor_nombre
        FROM lotes l
        JOIN usuarios u ON l.id_usuario = u.id_usuario
        WHERE l.peso_disponible_kg > 0
        ORDER BY l.fecha_registro DESC
    """
    return db.execute(query, fetch=True)

def obtener_por_usuario(usuario_id):
    db = DatabaseSingleton()
    query = """
        SELECT id_lote, especie, peso_disponible_kg, precio_kg, fecha_registro
        FROM lotes
        WHERE id_usuario = %s
        ORDER BY fecha_registro DESC
    """
    return db.execute(query, (usuario_id,), fetch=True)

def obtener_disponibles(categoria=None):
    db = DatabaseSingleton()
    query = """
        SELECT l.id_lote, l.especie, l.peso_disponible_kg, l.precio_kg, l.categoria,
               u.nombre AS proveedor_nombre
        FROM lotes l
        JOIN usuarios u ON l.id_usuario = u.id_usuario
        WHERE l.peso_disponible_kg > 0
    """
    params = []
    if categoria:
        query += " AND l.categoria = %s"
        params.append(categoria)
    query += " ORDER BY l.fecha_registro DESC"
    return db.execute(query, tuple(params), fetch=True)


def crear_lote(usuario_id, especie, categoria, peso_kg, precio_kg):
    db = DatabaseSingleton()
    query = """
        INSERT INTO lotes (id_usuario, especie, categoria, peso_disponible_kg, precio_kg, fecha_registro)
        VALUES (%s, %s, %s, %s, %s, NOW())
        RETURNING id_lote
    """
    resultado = db.execute(query, (usuario_id, especie, categoria, peso_kg, precio_kg), fetch=True)
    return resultado[0]["id_lote"] if resultado else None