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
        AND estado = 'abierto'
    """)
    eventos = cursor.fetchone()["total"]

    # Organizadores
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM organizadores
    """)
    organizadores = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        visitas_total=visitas_total,
        visitas_hoy=visitas_hoy,
        inscriptos_total=inscriptos_total,
        inscriptos_hoy=inscriptos_hoy,
        eventos=eventos,
        organizadores=organizadores
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