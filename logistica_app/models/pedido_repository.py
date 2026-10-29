from .db_singleton import DatabaseSingleton

def crear_pedido(id_lote, id_usuario, kg_solicitados):
    db = DatabaseSingleton()
    conn = db.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Stock y precio del lote
            cursor.execute(
                "SELECT peso_disponible_kg, precio_kg FROM lotes WHERE id_lote = %s",
                (id_lote,))
            row = cursor.fetchone()
            if not row:
                raise Exception("El lote ya no existe.")
            stock_actual = float(row[0])
            precio_kg = float(row[1])

            if stock_actual < kg_solicitados:
                raise Exception(f"Stock insuficiente. Solo quedan {stock_actual} kg disponibles.")

            total = round(kg_solicitados * precio_kg, 2)

            # 2. Encabezado del pedido
            cursor.execute("""
                INSERT INTO pedidos (restaurante_id, total_estimado, estado, fecha_pedido)
                VALUES (%s, %s, 'pendiente', NOW())
                RETURNING id
            """, (id_usuario, total))
            pedido_id = cursor.fetchone()[0]

            # 3. Línea de detalle (qué lote y cuántos kg)
            cursor.execute("""
                INSERT INTO detalle_pedidos (pedido_id, lote_id, cantidad_kg, precio_unitario)
                VALUES (%s, %s, %s, %s)
            """, (pedido_id, id_lote, kg_solicitados, precio_kg))

            # 4. Descontar inventario del lote
            cursor.execute("""
                UPDATE lotes SET peso_disponible_kg = %s WHERE id_lote = %s
            """, (stock_actual - kg_solicitados, id_lote))

            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        raise e


def obtener_por_usuario(usuario_id):
    db = DatabaseSingleton()
    query = """
        SELECT p.id AS id_pedido, d.cantidad_kg AS kg_solicitados,
               p.estado, p.fecha_pedido,
               l.especie, l.precio_kg, l.categoria,
               (d.cantidad_kg * d.precio_unitario) AS total
        FROM pedidos p
        JOIN detalle_pedidos d ON d.pedido_id = p.id
        JOIN lotes l ON d.lote_id = l.id_lote
        WHERE p.restaurante_id = %s
        ORDER BY p.fecha_pedido DESC
    """
    return db.execute(query, (usuario_id,), fetch=True)