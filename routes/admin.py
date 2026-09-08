from flask import Blueprint, render_template, request, redirect, session
from db import get_db_connection
admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin")
def admin():
    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Visitas totales
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM visitas_evento
    """)
    visitas_total = cursor.fetchone()["total"]

    # Visitas hoy
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM visitas_evento
        WHERE DATE(fecha) = CURDATE()
    """)
    visitas_hoy = cursor.fetchone()["total"]

    
    # Inscriptos totales
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM inscripciones
    """)
    inscriptos_total = cursor.fetchone()["total"]

    # Inscriptos hoy
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM inscripciones
        WHERE DATE(fecha_inscripcion) = CURDATE()
    """)
    inscriptos_hoy = cursor.fetchone()["total"]

    # Eventos activos
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM eventos
        WHERE activo = 1
        AND publicado = 1
        AND fecha >= CURDATE()
    """)
    eventos = cursor.fetchone()["total"]

    # Organizadores
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM organizadores
    """)
    organizadores = cursor.fetchone()["total"]

        # Resumen de inscripciones por eventos activos
    cursor.execute("""
        SELECT
            e.id,
            e.nombre,
            e.fecha,
            o.nombre AS organizador,

            COUNT(i.id) AS total_inscriptos,

            SUM(
                CASE
                    WHEN i.estado_pago = 'pagado' THEN 1
                    ELSE 0
                END
            ) AS pagados,

            SUM(
                CASE
                    WHEN i.estado_pago = 'pendiente' THEN 1
                    ELSE 0
                END
            ) AS pendientes,

            SUM(
                CASE
                    WHEN i.estado_pago = 'vencido' THEN 1
                    ELSE 0
                END
            ) AS vencidos

        FROM eventos e

        LEFT JOIN organizadores o
            ON o.id = e.organizador_id

        LEFT JOIN inscripciones i
            ON i.evento_id = e.id

        WHERE e.activo = 1
        AND e.publicado = 1
        AND e.fecha >= CURDATE()
        

        GROUP BY
            e.id,
            e.nombre,
            e.fecha,
            o.nombre

        ORDER BY total_inscriptos DESC
    """)

    resumen_eventos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        visitas_total=visitas_total,
        visitas_hoy=visitas_hoy,
        inscriptos_total=inscriptos_total,
        inscriptos_hoy=inscriptos_hoy,
        eventos=eventos,
        organizadores=organizadores,
        resumen_eventos=resumen_eventos
    )
@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM administradores
            WHERE usuario=%s
            AND password=%s
            AND activo=1
        """, (usuario, password))

        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin:

            session["admin_id"] = admin["id"]
            session["admin_nombre"] = admin["nombre"]

            return redirect("/admin")

    return render_template("admin/login.html")
@admin_bp.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect("/admin/login")