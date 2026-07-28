from flask import Blueprint, render_template, request, redirect, session
from db import get_db_connection
admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin")
def admin():
    if "admin_id" not in session:
        return redirect("/admin/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM visitas_evento
    """)

    visitas = cursor.fetchone()["total"]

    # Inscriptos
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM inscripciones
    """)
    inscriptos = cursor.fetchone()["total"]

    # Eventos
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM eventos
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
        visitas=visitas,
        inscriptos=inscriptos,
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