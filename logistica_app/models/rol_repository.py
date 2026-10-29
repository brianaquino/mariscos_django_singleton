from .db_singleton import DatabaseSingleton

def obtener_todos():
    db = DatabaseSingleton()
    query = "SELECT id_rol, nombre_rol FROM roles ORDER BY id_rol"
    return db.execute(query, fetch=True)