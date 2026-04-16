from flask import Blueprint, request, redirect
from db import get_db_connection

pagos_bp = Blueprint("pagos", __name__)
@pagos_bp.route("/inscripcion/<numero>/pago", methods=["GET","POST"])
def registrar_pago(numero):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        monto = request.form.get("monto")
        metodo = request.form.get("metodo")
        estado = request.form.get("estado")

        cursor.execute("""
        INSERT INTO pagos (inscripcion_id, monto, metodo, estado)
        VALUES (
            (SELECT id FROM inscripciones WHERE numero_inscripcion=%s),
            %s, %s, %s 
        )
        """, (numero, monto, metodo, estado))

        # 🔥 sincronizar inscripción
        if estado == "aprobado":
            cursor.execute("""
            UPDATE inscripciones
            SET estado_pago = 'pagado'
            WHERE numero_inscripcion = %s
            """, (numero,))

        conn.commit()
        conn.close()

        return redirect(f"/inscripcion/{numero}?ok=1")

    return f"""
    <h2>Registrar pago</h2>
    <form method="POST">

        Monto:<br>
        <input type="number" name="monto"><br><br>

        Estado:<br>
        <select name="estado">
            <option value="aprobado">Aprobado</option>
            <option value="pendiente">Pendiente</option>
        </select><br><br>

        Método:<br>
        <select name="metodo">
            <option value="manual">Manual</option>
            <option value="efectivo">Efectivo</option>
            <option value="transferencia">Transferencia</option>
        </select><br><br>

        <button>Guardar pago</button>
    </form>
    """