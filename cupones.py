"""Coupon-use validation shared by public and organizer registration flows."""


# Pending reservations and confirmed registrations consume one use. An unpaid
# expired reservation releases its use, while a confirmed payment remains a use
# even if the inscription is marked vencido after a stock issue.
CONDICION_USO_CUPON = """
(
    i.estado_pago IN ('pendiente', 'pagado', 'aprobado', 'bonificado', 'gratis')
    OR EXISTS (
        SELECT 1
        FROM pagos p
        WHERE p.inscripcion_id = i.id
          AND p.estado IN ('pagado', 'aprobado')
    )
)
"""


def reservar_uso_cupon(cursor, evento_id, clave):
    """Lock a coupon and check its cap inside the registration transaction.

    The caller must keep this transaction open until inserting the inscription
    with the returned ``cupon_id``.
    """
    cursor.execute("""
        SELECT id, max_usos
        FROM cupones
        WHERE evento_id = %s
          AND UPPER(clave) = UPPER(%s)
          AND activo = 1
          AND CURDATE() BETWEEN fecha_desde AND fecha_hasta
        LIMIT 1
        FOR UPDATE
    """, (evento_id, clave))
    cupon = cursor.fetchone()
    if not cupon:
        return None, "invalido"

    max_usos = cupon["max_usos"]
    if max_usos:
        # Every registration flow locks this coupon row before counting. This
        # locking read sees current committed rows after waiting, including
        # under MySQL's default REPEATABLE READ isolation level.
        cursor.execute("""
            SELECT i.id
            FROM inscripciones i
            WHERE i.cupon_id = %s
              AND {condicion}
            FOR UPDATE
        """.format(condicion=CONDICION_USO_CUPON), (cupon["id"],))
        usados = len(cursor.fetchall())
        if usados >= int(max_usos):
            return None, "agotado"

    return cupon["id"], None
