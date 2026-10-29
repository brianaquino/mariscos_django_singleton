# AHORA (dos puntos = sube al paquete padre, logistica_app):
from .db_singleton import DatabaseSingleton
def obtener_por_email(email):
    db = DatabaseSingleton()
    query = """
        SELECT id_usuario, nombre, email, password_hash, id_rol 
        FROM usuarios WHERE email = %s
    """
    resultado = db.execute(query, (email,), fetch=True)
    return resultado[0] if resultado else None

def crear_usuario(nombre, email, password_hash, id_rol):
    db = DatabaseSingleton()
    query = """
        INSERT INTO usuarios (nombre, email, password_hash, id_rol, fecha_registro)
        VALUES (%s, %s, %s, %s, NOW())
    """
    db.execute(query, (nombre, email, password_hash, id_rol))