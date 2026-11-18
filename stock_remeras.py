"""Shared shirt inventory rules used by registration and organizer flows."""

from collections import Counter


ESTADOS_RESERVA_PERMANENTE = ("pagado", "aprobado", "bonificado", "gratis")


def normalizar_talle(talle):
    return (talle or "").strip().upper()


def presentacion_disponibilidad(stock, comprometidas):
    """Clamp displayed availability at zero and return any visible shortage."""
    stock = int(stock)
    comprometidas = int(comprometidas)
    faltante = max(comprometidas - stock, 0)
    return max(stock - comprometidas, 0), faltante


def _condicion_reserva(alias="i"):
    return f"""(
        {alias}.estado_pago IN ('pagado', 'aprobado', 'bonificado', 'gratis')
        OR EXISTS (
            SELECT 1
            FROM pagos pago_confirmado
            WHERE pago_confirmado.inscripcion_id = {alias}.id
              AND pago_confirmado.estado IN ('aprobado', 'pagado')
        )
        OR (
            {alias}.estado_pago = 'pendiente'
            AND {alias}.fecha_inscripcion >= DATE_SUB(NOW(), INTERVAL 15 DAY)
        )
    )"""


def obtener_talles_comprometidos(
    cursor, evento_id, bloquear=False, excluir_inscripcion_id=None
):
    """Count each participant once, using participant rows as the source of truth.

    Legacy registrations with no rows in ``inscripcion_participantes`` fall
    back to ``inscripciones.talle_remera``. Pending registrations reserve for
    15 days; paid, approved, bonified, and free registrations remain counted.
    """
    bloqueo = " FOR UPDATE" if bloquear else ""
    condicion = _condicion_reserva()
    exclusion = ""
    parametros = [evento_id]
    if excluir_inscripcion_id is not None:
        exclusion = " AND i.id <> %s"
        parametros.append(excluir_inscripcion_id)

    # When participant rows exist, count all of them and do not also count the
    # inscription's legacy top-level field.
    cursor.execute(f"""
        SELECT ip.talle_remera AS talle
        FROM inscripciones i
        JOIN inscripcion_participantes ip
          ON ip.inscripcion_id = i.id
        WHERE i.evento_id = %s
          AND {condicion}
          AND ip.talle_remera IS NOT NULL
          AND TRIM(ip.talle_remera) NOT IN ('', 'None')
          {exclusion}
        {bloqueo}
    """, tuple(parametros))
    filas = cursor.fetchall()

    # Compatibility for older registrations that predate participant rows.
    cursor.execute(f"""
        SELECT i.talle_remera AS talle
        FROM inscripciones i
        WHERE i.evento_id = %s
          AND {condicion}
          AND i.talle_remera IS NOT NULL
          AND TRIM(i.talle_remera) NOT IN ('', 'None')
          AND NOT EXISTS (
              SELECT 1
              FROM inscripcion_participantes ip
              WHERE ip.inscripcion_id = i.id
          )
          {exclusion}
        {bloqueo}
    """, tuple(parametros))
    filas.extend(cursor.fetchall())

    cantidades = Counter()
    for fila in filas:
        talle = normalizar_talle(fila.get("talle"))
        if talle:
            cantidades[talle] += 1
    return cantidades


def obtener_talles_inscripcion(cursor, inscripcion_id, bloquear=False):
    """Return participant sizes, falling back to the legacy inscription field."""
    bloqueo = " FOR UPDATE" if bloquear else ""
    cursor.execute(f"""
        SELECT talle_remera
        FROM inscripcion_participantes
        WHERE inscripcion_id = %s
        ORDER BY orden
        {bloqueo}
    """, (inscripcion_id,))
    filas = cursor.fetchall()
    if filas:
        return [
            normalizar_talle(fila.get("talle_remera"))
            for fila in filas
            if normalizar_talle(fila.get("talle_remera"))
        ]

    cursor.execute(f"""
        SELECT talle_remera
        FROM inscripciones
        WHERE id = %s
        {bloqueo}
    """, (inscripcion_id,))
    fila = cursor.fetchone()
    talle = normalizar_talle(fila.get("talle_remera") if fila else None)
    return [talle] if talle else []


def guardar_talle_participante(cursor, inscripcion_id, orden, talle):
    """Persist a shirt size on one participant row, never on the whole team."""
    cursor.execute("""
        UPDATE inscripcion_participantes
        SET talle_remera = %s
        WHERE inscripcion_id = %s AND orden = %s
    """, (talle, inscripcion_id, orden))


def contar_seleccionados(talles):
    return Counter(
        talle for talle in (normalizar_talle(t) for t in talles) if talle
    )


def evaluar_disponibilidad(talles, stock_por_talle, comprometidos,
                           permitir_inactivos=None,
                           permitir_sin_configuracion=False):
    """Pure inventory check shared by endpoints and unit tests."""
    solicitados = contar_seleccionados(talles)
    permitir_inactivos = permitir_inactivos or Counter()

    for talle, cantidad in solicitados.items():
        fila = stock_por_talle.get(talle)
        if not fila:
            if permitir_sin_configuracion and cantidad <= permitir_inactivos[talle]:
                continue
            return False, "sin_configuracion"
        if not fila.get("activo") and cantidad > permitir_inactivos[talle]:
            return False, "inactivo"
        if comprometidos[talle] + cantidad > int(fila["stock"]):
            return False, "agotado"
    return True, None


def evaluar_cambio_talles(talles_nuevos, talles_anteriores,
                          stock_por_talle, comprometidos):
    """Allow existing shortages to remain or improve, never increase per size."""
    nuevos = contar_seleccionados(talles_nuevos)
    anteriores = contar_seleccionados(talles_anteriores)

    for talle in sorted(set(nuevos) | set(anteriores)):
        cantidad_nueva = nuevos[talle]
        cantidad_anterior = anteriores[talle]
        fila = stock_por_talle.get(talle)

        # Missing/ambiguous historic stock configuration may be preserved,
        # but cannot be used to add another committed shirt.
        if not fila:
            if cantidad_nueva > cantidad_anterior:
                return False, "sin_configuracion"
            continue

        if not fila.get("activo") and cantidad_nueva > cantidad_anterior:
            return False, "inactivo"

        stock = int(fila["stock"])
        demanda_anterior = comprometidos[talle] + cantidad_anterior
        demanda_nueva = comprometidos[talle] + cantidad_nueva
        faltante_anterior = max(demanda_anterior - stock, 0)
        faltante_nuevo = max(demanda_nueva - stock, 0)
        if faltante_nuevo > faltante_anterior:
            return False, "agotado"

    return True, None


def estado_revision_pago(pago_confirmado, incluye_remera, reserva_disponible):
    """Classify a confirmed payment without assuming every vencido is a shirt issue."""
    if not pago_confirmado:
        return None
    if incluye_remera and not reserva_disponible:
        return "revisar_remera"
    return "revisar_inscripcion"


def reserva_requiere_reactivacion(estado_pago, vencida_por_fecha=False):
    """An expired pending reservation is reactivatable before cleanup updates its state."""
    return estado_pago == "vencido" or (
        estado_pago == "pendiente" and bool(vencida_por_fecha)
    )


def consultar_stock_talles(
    cursor, evento_id, talles, excluir_inscripcion_id=None,
    permitir_inactivos=None, permitir_sin_configuracion=False,
):
    """Read-only availability check for review screens and accreditation."""
    solicitados = contar_seleccionados(talles)
    stock_por_talle = {}
    for talle in sorted(solicitados):
        cursor.execute("""
            SELECT id, talle, stock, activo
            FROM stock_remeras
            WHERE evento_id = %s AND UPPER(talle) = %s
        """, (evento_id, talle))
        filas = cursor.fetchall()
        if len(filas) != 1:
            if (not filas and permitir_sin_configuracion
                    and solicitados[talle] <= (permitir_inactivos or Counter())[talle]):
                continue
            return False, "sin_configuracion"
        stock_por_talle[talle] = {
            "stock": filas[0]["stock"],
            "activo": bool(filas[0]["activo"]),
        }

    comprometidos = obtener_talles_comprometidos(
        cursor, evento_id, excluir_inscripcion_id=excluir_inscripcion_id
    )
    return evaluar_disponibilidad(
        talles, stock_por_talle, comprometidos, permitir_inactivos,
        permitir_sin_configuracion,
    )


def validar_stock_talles(
    cursor, evento_id, talles, excluir_inscripcion_id=None,
    permitir_inactivos=None, permitir_sin_configuracion=False,
):
    """Lock selected stock rows, then validate their aggregate demand."""
    solicitados = contar_seleccionados(talles)
    stock_por_talle = {}

    # Stable lock ordering serializes simultaneous registrations that want the
    # same size and reduces deadlock risk for pairs selecting different sizes.
    for talle in sorted(solicitados):
        cursor.execute("""
            SELECT id, talle, stock, activo
            FROM stock_remeras
            WHERE evento_id = %s AND UPPER(talle) = %s
            FOR UPDATE
        """, (evento_id, talle))
        filas = cursor.fetchall()
        if len(filas) != 1:
            if (
                not filas
                and permitir_sin_configuracion
                and solicitados[talle] <= (permitir_inactivos or Counter())[talle]
            ):
                continue
            return False, "sin_configuracion"
        fila = filas[0]
        stock_por_talle[talle] = {
            "stock": fila["stock"],
            "activo": bool(fila["activo"]),
        }

    comprometidos = obtener_talles_comprometidos(
        cursor,
        evento_id,
        bloquear=True,
        excluir_inscripcion_id=excluir_inscripcion_id,
    )
    return evaluar_disponibilidad(
        talles,
        stock_por_talle,
        comprometidos,
        permitir_inactivos,
        permitir_sin_configuracion,
    )


def validar_cambio_stock_talles(
    cursor, evento_id, talles_nuevos, talles_anteriores,
    excluir_inscripcion_id,
):
    """Lock all relevant sizes and reject only changes that worsen shortages."""
    nuevos = contar_seleccionados(talles_nuevos)
    anteriores = contar_seleccionados(talles_anteriores)
    stock_por_talle = {}

    for talle in sorted(set(nuevos) | set(anteriores)):
        cursor.execute("""
            SELECT id, talle, stock, activo
            FROM stock_remeras
            WHERE evento_id = %s AND UPPER(talle) = %s
            FOR UPDATE
        """, (evento_id, talle))
        filas = cursor.fetchall()
        if len(filas) == 1:
            stock_por_talle[talle] = {
                "stock": filas[0]["stock"],
                "activo": bool(filas[0]["activo"]),
            }
        elif nuevos[talle] > anteriores[talle]:
            return False, "sin_configuracion"

    comprometidos = obtener_talles_comprometidos(
        cursor,
        evento_id,
        bloquear=True,
        excluir_inscripcion_id=excluir_inscripcion_id,
    )
    return evaluar_cambio_talles(
        talles_nuevos, talles_anteriores, stock_por_talle, comprometidos
    )
