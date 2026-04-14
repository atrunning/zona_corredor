from flask import Flask, request
from db import get_db_connection
from datetime import date

app = Flask(__name__)
app.secret_key = "12356"
from routes.organizador import organizador_bp
from routes.eventos import eventos_bp
from flask import session, redirect
import re
from routes.pagos import pagos_bp
app.register_blueprint(pagos_bp)
import os
import mercadopago

import requests
from flask import request

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
print("🔥 BASE_URL EN PRODUCCION:", BASE_URL)

def slugify(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-z0-9\s-]', '', texto)
    texto = texto.replace(" ", "-")
    return texto

app.register_blueprint(organizador_bp)
app.register_blueprint(eventos_bp)
print("🔥 VERSION NUEVA 🔥")
def layout(contenido, menu=True, evento_id=None, eventos=None):


    menu_html = ""

    if menu:
        menu_html = """
        <div style="
        width:200px;
        background:#f0f0f0;
        padding:20px;
        height:100vh;
        ">
        <h3>Menú</h3>
        """
        

        if evento_id:
            menu_html += f"""
            <a href="/organizador">📋 Eventos</a>
            <a href="/evento/{evento_id}/panel">Panel</a><br><br>
            <a href="/evento/{evento_id}/inscriptos">Inscriptos</a><br><br>
            <a href="/evento/{evento_id}/exportar">Exportar inscriptos</a><br><br>
            <a href="/evento/{evento_id}/exportar_seguro">Exportar seguro</a><br><br>
            <a href="/evento/{evento_id}/reporte_remeras">Reporte de remeras</a><br><br>

            <hr>

            <b>💳 MercadoPago</b><br>
            <a href="/conectar_mp">🔗 Conectar MercadoPago</a><br><br>
            """
            

        menu_html += """
        

        

        </div>
        """
    

    return f"""
    <html>
    <body style="font-family:Arial;margin:0">

    <div style="
    background:#222;
    color:white;
    padding:10px 20px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    ">

    <div style="display:flex; align-items:center; gap:15px;">
        <img src="/static/logo.png" style="
        height:60px;
        background:white;
        padding:px;
        border-radius:10px;
        box-shadow:0 2px 6px rgba(0,0,0,0.3);
        ">

        <span style="
        font-size:22px;
        font-weight:bold;
        letter-spacing:1px;
        ">
        Zona Corredor
        </span>
    </div>

    <div>
        <a href="mailto:zonacorredor@gmail.com" style="color:white;margin-right:20px;text-decoration:none">
            📧 zonacorredor@gmail.com
        </a>

        <a href="/" style="color:white;margin-right:20px;text-decoration:none">Eventos</a>
        <a href="/organizador" style="color:white;text-decoration:none">Organizadores</a>
    </div>

    </div>

    

    <div style="display:flex">

    {menu_html}

    <div style="padding:20px;width:100%">
    {contenido}
    </div>

    </div>
    
    </body>
    </html>
    """


from urllib.parse import urlencode
@app.route("/")
def home():
    return "Zona Corredor funcionando 🚀"

@app.route("/conectar_mp")
def conectar_mp():
    organizador_id = session.get("organizador_id")

    params = {
        "client_id": "7256036373469790",
        "response_type": "code",
        "scope": "read write offline_access",
        "state": str(organizador_id),
        "redirect_uri": f"{BASE_URL}/mp_callback"
    }

    url = "https://auth.mercadopago.com/authorization?" + urlencode(params)

    return redirect(url)

@app.route("/mp_callback")
def mp_callback():
    code = request.args.get("code")
    organizador_id = request.args.get("state")

    if not code:
        return f"ERROR MP: {request.args}"

    url = "https://api.mercadopago.com/oauth/token"

    payload = {
        "client_id": "7256036373469790",
        "client_secret": os.getenv("MP_CLIENT_SECRET"),
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": f"{BASE_URL}/mp_callback"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(url, data=payload, headers=headers)
    data = response.json()

    print("MP TOKEN:", data)

    if "access_token" not in data:
        return f"ERROR TOKEN: {data}"

    access_token = data["access_token"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE organizadores
    SET access_token_mp = %s
    WHERE id = %s
    """, (access_token, organizador_id))

    conn.commit()
    cursor.close()
    conn.close()

    # 👉 guardar en DB con organizador_id

    return "MP conectado correctamente 🎉"
@app.route("/")
def inicio():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Solo traemos eventos activos y futuros

    cursor.execute("""
    SELECT 
        e.id,
        e.nombre,
        e.fecha,
        e.lugar,
        e.provincia,
        e.hora,
        o.nombre AS organizador,
        e.imagen
    FROM eventos e
    LEFT JOIN organizadores o 
        ON e.organizador_id = o.id
    WHERE e.fecha >= CURDATE()
    AND e.activo = 1
    AND e.publicado = 1
    ORDER BY e.fecha ASC
    """)

    eventos = cursor.fetchall()
    cursor.close()
    conn.close()

    # Título principal
    salida = "<h1 style='text-align:center; color:#333; margin-top:30px;'>PRÓXIMOS EVENTOS</h1>"

    # CONTENEDOR FLEX: Esto alinea las tarjetas una al lado de la otra
    salida += """
    <div style='
        display: flex; 
        flex-wrap: wrap; 
        gap: 25px; 
        justify-content: center; 
        padding: 20px;
    '>
    """

    for e in eventos:
        imagen = e["imagen"] if e["imagen"] else "evento.jpg"
        
        # TARJETA INDIVIDUAL
        # ... dentro de tu bucle for e in eventos:

        salida += f"""
        <div style="
        position:relative;
        width:260px;
        background:#f8f8f8;
        border-radius:10px;
        overflow:hidden;
        box-shadow:0 3px 8px rgba(0,0,0,0.15);
        display:flex;
        flex-direction:column;
        ">
            <div style="position: relative;">
                <div style="
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    background: #28a745;
                    color: white;
                    padding: 5px 12px;
                    border-radius: 20px;
                    font-size: 11px;
                    font-weight: bold;
                    z-index: 10;
                ">
                    PRÓXIMO
                </div>
                <img src="/static/eventos/{imagen}" style="width:100%; height:180px; object-fit:cover; display:block;">
            </div>

            <div style="
                padding: 15px; 
                text-align: center; 
                display: flex; 
                flex-direction: column; 
                flex-grow: 1; /* Esto hace que este bloque ocupe todo el espacio sobrante */
            ">
                <b style="font-size: 18px; color: #222; min-height: 44px; display: block;">
                    {e['nombre']}
                </b>
                
                <p style="margin: 10px 0; color: #666; font-size: 14px;">
                    📍 {e['lugar']}<br>
                    ⏰ {e['hora']} hs<br>
                    👤 {e['organizador']}<br>
                    <span style="min-height: 1.2em; display: inline-block;">
                        {e['provincia'] if e['provincia'] else '&nbsp;'}
                    </span>
                </p>

                <div style="font-weight: bold; color: #1976d2; margin-bottom: 15px;">
                    📅 {e['fecha'].strftime('%d/%m/%Y')}
                </div>

                <div style="margin-top: auto;"> 
                    <a href="/evento/{e['id']}" style="
                        text-decoration: none;
                        background: #222;
                        color: white;
                        padding: 10px 25px;
                        border-radius: 5px;
                        display: inline-block;
                        font-size: 14px;
                        width: 80%; /* Para que todos tengan el mismo ancho si quieres */
                    ">
                        Ver evento
                    </a>
                </div>
            </div>
        </div>
        """
    salida += "</div>" # Cierre del contenedor flex

    return layout(salida, menu=False)

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return """
    <div style="max-width:400px;margin:80px auto;font-family:Arial">

    <h2 style="text-align:center">🔐 Ingresar</h2>

    <form method="POST" style="display:flex;flex-direction:column;gap:10px">

    <input type="email" name="email" placeholder="Email" required style="padding:10px">

    <input type="password" name="password" placeholder="Contraseña" required style="padding:10px">

    <button style="padding:10px;background:#1976d2;color:white;border:none;border-radius:5px">
    Entrar
    </button>

    </form>

    <div style="margin-top:20px;text-align:center">

    <a href="/registro">
        <button style="
            padding:10px;
            background:#4caf50;
            color:white;
            border:none;
            border-radius:5px;
            width:100%;
            cursor:pointer;
        ">
            ➕ Crear cuenta
        </button>
    </a>

    </div>

    </div>
    """

    email = request.form["email"]
    password = request.form.get("password", "")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM organizadores WHERE email = %s", (email,))
    org = cursor.fetchone()

    # ---------------------------
    # ❌ SI NO EXISTE
    # ---------------------------
    if not org:
        return """
        <h2>❌ Email no registrado</h2>
        <a href="/registro">Crear cuenta</a>
        """

    # ---------------------------
    # ❌ PASSWORD INCORRECTA
    # ---------------------------
    if org["password"] != password:
        return """
        <h2>❌ Email o contraseña incorrectos</h2>
        <a href="/login">Volver</a>
        """

    # ---------------------------
    # ✅ LOGIN OK
    # ---------------------------
    session["organizador_id"] = org["id"]

    cursor.close()
    conn.close()

    return """

<script>
window.location.href="/organizador"
</script>
"""

    # ---------------------------
    # SI NO EXISTE → CREAR
    # ---------------------------
    if not org:

        cursor.execute("""
            INSERT INTO organizadores (nombre, email, password)
            VALUES (%s, %s, %s)
        """, (nombre if nombre else "Organizador", email, password))

        conn.commit()
        organizador_id = cursor.lastrowid

    # ---------------------------
    # SI EXISTE → VALIDAR PASSWORD
    # ---------------------------
    else:

        if org["password"] != password:
            return "<h2>❌ Contraseña incorrecta</h2>"

        organizador_id = org["id"]

    cursor.close()
    conn.close()

    session["organizador_id"] = organizador_id

    return """
    <script>
    window.location.href="/organizador"
    </script>
    """
    # guardar sesión
    session["organizador_id"] = organizador_id

    return """
    <script>
    window.location.href="/organizador"
    </script>
    """
@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "GET":
        return """
        <div style="max-width:400px;margin:80px auto;font-family:Arial">

        <h2 style="text-align:center">📝 Crear cuenta</h2>

        <form method="POST" style="display:flex;flex-direction:column;gap:10px">

        <input type="text" name="nombre" placeholder="Nombre" required style="padding:10px">

        <input type="email" name="email" placeholder="Email" required style="padding:10px">

        <input type="password" name="password" placeholder="Password" required style="padding:10px">

        <input type="text" name="telefono" placeholder="Teléfono" style="padding:10px">

        <input type="text" name="contacto" placeholder="Contacto (Responsable)" style="padding:10px">

        <button style="padding:10px;background:#4caf50;color:white;border:none;border-radius:5px">
        Crear cuenta
        </button>

        </form>

        </div>
        """
    contacto = request.form.get("contacto")
    nombre = request.form["nombre"]
    email = request.form["email"]
    password = request.form["password"]
    telefono = request.form.get("telefono")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # verificar si ya existe
    cursor.execute("SELECT id FROM organizadores WHERE email = %s", (email,))
    existe = cursor.fetchone()

    if existe:
        return "<h2>❌ Ese email ya está registrado</h2><a href='/login'>Volver</a>"

    cursor.execute("""
        INSERT INTO organizadores (nombre, email, password, telefono, contacto)
        VALUES (%s, %s, %s, %s, %s)
    """, (nombre, email, password, telefono, contacto))

    conn.commit()
    organizador_id = cursor.lastrowid

    cursor.close()
    conn.close()

    session["organizador_id"] = organizador_id

    return """
    <script>
    window.location.href="/organizador"
    </script>
    """    

@app.route("/evento/<int:evento_id>")
def ver_evento(evento_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            e.*,
            o.nombre AS organizador
        FROM eventos e
        LEFT JOIN organizadores o
            ON e.organizador_id = o.id
        WHERE e.id = %s
    """, (evento_id,))

    evento = cursor.fetchone()
    

    imagen = evento["imagen"] if evento["imagen"] else "evento.jpg"

    cursor.execute("""
    SELECT
        id,
        nombre,
        precio,
        es_gratis,
        incluye_remera,
        cupo,
        fecha_inicio_inscripcion,
        fecha_fin_inscripcion
    FROM distancias
    WHERE evento_id = %s
    """,(evento_id,))
    distancias = cursor.fetchall()

    cursor.execute("SELECT DATABASE()")
    print("DB:", cursor.fetchone())

    cursor.execute("SHOW COLUMNS FROM distancias")
    print("COLUMNAS:", cursor.fetchall())
   
    salida = f"""
    <div style="max-width:1000px;margin:auto;padding:20px">
    """
    salida += f"""
    <div style="
    display:flex;
    gap:20px;
    align-items:stretch;
    flex-wrap:wrap;
    ">

    <div style="flex:1; min-width:300px">
        <img src="/static/eventos/{imagen}"
        style="
        width:100%;
        height:280px;
        object-fit:cover;
        border-radius:10px;
        ">
    </div>
    """

    if evento.get("latitud") and evento.get("longitud"):
        salida += f"""
        <div style="flex:1">

            <iframe
            src="https://www.google.com/maps?q={evento['latitud']},{evento['longitud']}&output=embed"
            width="100%"
            height="320"
            style="border:0;border-radius:10px"
            loading="lazy">
            </iframe>

            <div style="margin-top:10px;text-align:center">

                <a href="https://www.google.com/maps?q={evento['latitud']},{evento['longitud']}"
                target="_blank"
                style="
                display:inline-block;
                padding:10px 15px;
                background:#1976d2;
                color:white;
                border-radius:8px;
                text-decoration:none;
                font-weight:bold
                ">
                📍 Ver en Google Maps
                </a>

            </div>

        </div>
    """
       

    salida += """
    </div>
    """

    salida += f"""
    <h1 style="text-align:center;margin-top:20px">
    {evento['nombre']}
    </h1>

    <div style="display:flex; justify-content:center; gap:20px; margin-top:10px; font-size:18px; flex-wrap:wrap; text-align:center;">

    <div>📅 {evento['fecha'].strftime('%d/%m/%Y')}</div>
    <div>📍 {evento.get('direccion') or evento['lugar']}</div>
    <div>⏰ {evento['hora']}</div>
    <div>👤 Organiza: {evento['organizador']}</div>
    </div>

    <div style="text-align:center;margin-top:25px">

    <button onclick="abrirDistancias()" style="
    padding:12px 28px;
    background:#2e7d32;
    color:white;
    border:none;
    border-radius:8px;
    font-size:18px;
    cursor:pointer;
    ">
    INSCRIBIRME
    </button>

    </div>
    """    
    descripcion = evento["descripcion"].replace("\n","<br>") if evento["descripcion"] else ""

    salida += f"""
    <div style="max-width:900px;margin:auto;margin-top:30px">

    <h2>Información del evento</h2>

    <div style="
    background:#f8f8f8;
    padding:20px;
    border-radius:10px;
    line-height:1.6;
    border:1px solid #ddd;
    min-height:120px;
    ">

    {descripcion}

    </div>
    </div>
    """
    

    salida += """
    <div style="
        max-width:900px;
        margin:auto;
        margin-top:30px;
        border-radius:12px;
        overflow:hidden;
        border:1px solid #ddd;
        background:white;
        box-shadow:0 4px 8px rgba(0,0,0,0.1);
        position:relative;
    ">
    """
    

        
    salida += "</div>"

    salida += """
    <div id="modalDistancias" style="
    display:none;
    position:fixed;
    top:0;
    left:0;
    width:100%;
    height:100%;
    background:rgba(0,0,0,0.5);
    justify-content:center;
    align-items:center;
    z-index:999;
    ">

    <div style="
    background:white;
    padding:25px;
    border-radius:10px;
    width:400px;
    max-width:90%;
    ">

    <h3>Elegí distancia</h3>
    """

    # calcular inscriptos y disponibles
    cursor.execute("""
        SELECT distancia_id, COUNT(*) as inscriptos
        FROM inscripciones
        WHERE evento_id = %s
        GROUP BY distancia_id
    """, (evento_id,))

    conteo = {row["distancia_id"]: row["inscriptos"] for row in cursor.fetchall()}

    
    for d in distancias:

        hoy = date.today()

        precio = "Gratis" if d["es_gratis"] else f"${int(d['precio']):,}".replace(",", ".")
        remera = "👕 incluye remera" if d["incluye_remera"] else ""

        inicio = d["fecha_inicio_inscripcion"]
        fin = d["fecha_fin_inscripcion"]

        inscripcion_abierta = True

        if inicio and hoy < inicio:
            inscripcion_abierta = False

        if fin and hoy > fin:
            inscripcion_abierta = False

        # 🔥 ESTO FALTABA
        inscriptos = conteo.get(d["id"], 0)
        disponibles = max(d["cupo"] - inscriptos, 0)

        if inscripcion_abierta and disponibles > 0:
            boton = ...


            
            if inscripcion_abierta and disponibles > 0:

                boton = f"""
                <a href="/evento/{evento_id}/inscribirse?distancia={d['id']}">
                    <button style="
                    padding:10px 16px;
                    background:#2e7d32;
                    color:white;
                    border:none;
                    border-radius:5px;
                    cursor:pointer;
                    ">
                    Inscribirme
                    </button>
                </a>
                """

            else:

                boton = """
                <button style="
                padding:10px 16px;
                background:#ccc;
                color:#666;
                border:none;
                border-radius:5px;
                cursor:not-allowed;
                opacity:0.6;
                ">
                Cupo completo
                </button>
                """
            salida += f"""
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                padding:15px;
                margin-bottom:12px;
                border:1px solid #ddd;
                border-radius:6px;
                background:#fafafa;
            ">

                <div>
                    <b>{d['nombre']}</b><br>
                    Precio: {precio}<br>
                    {remera}
                </div>

                <div>
                    {boton}
                </div>

            </div>
            """
    cursor.close()
    conn.close()
    

    salida += """
    <button onclick="cerrarDistancias()" style="
    margin-top:15px;
    padding:8px 12px;
    border:none;
    background:#ccc;
    border-radius:5px;
    cursor:pointer;
    ">
    Cerrar
    </button>

    </div>
    </div>
    """
    
    salida += """
    <script>

    function abrirDistancias(){
    document.getElementById("modalDistancias").style.display="flex";
    }

    function cerrarDistancias(){
    document.getElementById("modalDistancias").style.display="none";
    }

    </script>
    """
    return layout(salida, menu=False)

@app.route("/eventos")
def listar_eventos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, nombre, fecha, lugar FROM eventos")
    eventos = cursor.fetchall()

    cursor.close()
    conn.close()

    salida = "<h1>Eventos disponibles</h1>"

    for e in eventos:
        salida += f"<p>{e['id']} - {e['nombre']} - {e['fecha']} - {e['lugar']}</p>"

    return salida

@app.route("/evento/<int:evento_id>/reporte_remeras")
def reporte_remeras(evento_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT talle_remera, COUNT(*) AS cantidad
    FROM inscripciones
    WHERE evento_id = %s
    GROUP BY talle_remera
    ORDER BY talle_remera
    """,(evento_id,))

    talles = cursor.fetchall()

    cursor.close()
    conn.close()

    salida = "<h1>Reporte de remeras</h1>"

    salida += "<table border='1' cellpadding='8'>"
    salida += "<tr><th>Talle</th><th>Cantidad</th></tr>"

    for t in talles:

        salida += f"""
        <tr>
        <td>{t['talle_remera']}</td>
        <td>{t['cantidad']}</td>
        </tr>
        """

    salida += "</table>"

    return layout(salida)




@app.route("/evento/<int:evento_id>/inscribirse", methods=["GET", "POST"])
def inscribirse(evento_id):
    distancia_id = request.args.get("distancia")

    if not distancia_id:
        return "Distancia no especificada"
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT cupo, incluye_remera,
    (SELECT COUNT(*) FROM inscripciones
    WHERE distancia_id=%s AND evento_id=%s) AS inscriptos
    FROM distancias
    WHERE id=%s
    """, (distancia_id, evento_id, distancia_id))

    datos = cursor.fetchone()

    cursor.close()
    conn.close()

    if datos["inscriptos"] >= datos["cupo"]:
        return f"""
        <h2>Inscripciones completas</h2>
        <p>Esta distancia ya no tiene lugares disponibles.</p>

        <a href="/evento/{evento_id}">
            <button>Volver al evento</button>
        </a>
        """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT nombre FROM eventos WHERE id = %s", (evento_id,))
    evento = cursor.fetchone()

    nombre_evento = evento["nombre"] if evento else f"Evento {evento_id}"

    if request.method == "GET":
        return f"""
        <div style="max-width:400px;margin:80px auto;font-family:Arial;text-align:center">

        <h2 style="margin-bottom:10px">🏁 Inscribite</h2>

        <div style="color:#555;margin-bottom:25px">
        Evento: <b>{nombre_evento}</b>
        </div>

        <form method="POST" style="display:flex;flex-direction:column;gap:15px">

        <input type="hidden" name="distancia_id" value="{distancia_id}">

        <input type="text" name="dni" placeholder="Ingresá tu DNI"
        maxlength="8"
        oninput="this.value=this.value.replace(/[^0-9]/g,'')"
        style="
        padding:12px;
        font-size:16px;
        border-radius:6px;
        border:1px solid #ccc;
        text-align:center;
        "
        required>

        <button type="submit" name="accion" value="buscar"
        style="
        padding:12px;
        font-size:16px;
        background:#2e7d32;
        color:white;
        border:none;
        border-radius:6px;
        cursor:pointer;
        ">
        Continuar inscripción
        </button>

        </form>

        <div style="margin-top:20px;color:#777;font-size:13px">
        Ingresá tu DNI para buscar o crear tu registro
        </div>

        </div>
        """
           
    accion = request.form.get("accion")

    # --------------------------------------
    # BUSCAR DNI
    # --------------------------------------
    if accion == "buscar":

        dni = request.form["dni"].replace(".", "").replace(" ", "")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM personas WHERE dni = %s", (dni,))
        persona = cursor.fetchone()

        # si no existe persona, crear estructura vacía
        if not persona:
            persona = {
                "id": "",
                "dni": dni,
                "nombre": "",
                "apellido": "",
                "email": "",
                "celular": "",
                "fecha_nac": "",
                "genero": "",
                "pais_id": None,
                "provincia_id": None,
                "ciudad": ""
            }
        cursor.execute(
            "SELECT id, nombre FROM distancias WHERE evento_id = %s",
            (evento_id,)
        )
        distancias = cursor.fetchall()

        cursor.execute("SELECT id, nombre FROM teams WHERE activo = 1 ORDER BY nombre")
        teams = cursor.fetchall()

        cursor.execute("SELECT id, nombre FROM provincias ORDER BY nombre")
        provincias = cursor.fetchall()

        cursor.execute("SELECT id, nombre FROM paises ORDER BY nombre")
        paises = cursor.fetchall()

        # obtener distancia seleccionada
        distancia_id = request.form["distancia_id"]

        cursor.execute("""
        SELECT nombre, incluye_remera
        FROM distancias
        WHERE id = %s AND evento_id = %s
        """, (distancia_id, evento_id))

        distancia = cursor.fetchone()
        
        cursor.close()
        conn.close()

        salida = f"""
        <div style="max-width:600px;margin:40px auto;font-family:Arial">

        <h2 style="text-align:center;margin-bottom:10px">🏃 Datos del corredor</h2>

        <div style="text-align:center;color:#555;margin-bottom:25px">
        Distancia: <b>{distancia['nombre']}</b>
        </div>

        <form method="POST" style="display:flex;flex-direction:column;gap:15px">

        <input type="hidden" name="distancia_id" value="{distancia_id}">
        <input type="hidden" name="accion" value="confirmar">
        <input type="hidden" name="persona_id" value="{persona['id']}">

        <h3>Identificación</h3>

        <input type="text" name="dni" value="{dni}" pattern="[0-9]{{7,8}}" maxlength="8" required
        placeholder="DNI"
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <input type="text" name="nombre" value="{persona['nombre']}" placeholder="Nombre"
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <input type="text" name="apellido" value="{persona['apellido']}" placeholder="Apellido"
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <input type="email" name="email" value="{persona['email']}" placeholder="Email" required
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <input type="email" name="email_confirmar" placeholder="Confirmar email" required
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <input type="text" name="celular" value="{persona['celular']}" placeholder="Celular"
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <input type="date" name="fecha_nacimiento" value="{persona.get('fecha_nac','')}" required
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <input type="number" name="edad" min="1" max="100" placeholder="Edad"
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <select name="genero" style="padding:10px;border-radius:6px;">
            <option value="">Seleccionar género</option>
            <option value="M" {"selected" if persona.get("genero")=="M" else ""}>Masculino</option>
            <option value="F" {"selected" if persona.get("genero")=="F" else ""}>Femenino</option>
            <option value="X" {"selected" if persona.get("genero")=="X" else ""}>Otro</option>
        </select>

        <h3>Ubicación</h3>
        """

        # 🌍 País
        salida += '<select name="pais_id" style="padding:10px;border-radius:6px;">'
        for p in paises:
            selected = "selected" if persona.get("pais_id") == p["id"] else ""
            salida += f"<option value='{p['id']}' {selected}>{p['nombre']}</option>"
        salida += "</select>"

        # 🏙 Provincia
        salida += '<select name="provincia_id" style="padding:10px;border-radius:6px;">'
        for p in provincias:
            selected = "selected" if persona.get("provincia_id") == p["id"] else ""
            salida += f"<option value='{p['id']}' {selected}>{p['nombre']}</option>"
        salida += "</select>"

        salida += f"""
        <input type="text" name="ciudad" value="{persona['ciudad']}" placeholder="Ciudad"
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <h3>Redes (opcional)</h3>

        <input type="text" name="instagram" placeholder="Instagram"
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <input type="text" name="strava" placeholder="Strava"
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <input type="text" name="facebook" placeholder="Facebook"
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">
        """

        # 👕 Remera
        if str(distancia.get("incluye_remera")) == "1":
            salida += """
            <h3>Talle de remera</h3>
            <select name="remera" required style="padding:10px;border-radius:6px;">
                <option value="">Seleccionar</option>
                <option>XS</option>
                <option>S</option>
                <option>M</option>
                <option>L</option>
                <option>XL</option>
                <option>XXL</option>
            </select>
            """

        # 👥 Team
        salida += '<h3>Equipo</h3>'
        salida += '<select name="team_id" style="padding:10px;border-radius:6px;">'
        salida += "<option value=''>-- Sin equipo --</option>"
        for t in teams:
            salida += f"<option value='{t['id']}'>{t['nombre']}</option>"
        salida += "</select>"

        salida += """
        <input type="text" name="team_nuevo" placeholder="O escribir nuevo equipo"
        style="padding:10px;border:1px solid #ccc;border-radius:6px;">

        <button type="submit"
        style="margin-top:20px;padding:14px;background:#2e7d32;color:white;border:none;border-radius:8px;font-size:16px;cursor:pointer;">
        Confirmar inscripción
        </button>

        </form>
        </div>
        """

        return salida

    # --------------------------------------
    # CONFIRMAR INSCRIPCIÓN
    # --------------------------------------
    
    if accion == "confirmar":

        distancia_id = request.form.get("distancia_id")

        if not distancia_id:
            return "Error: distancia perdida 😈"

         
        from datetime import date, datetime

        fecha_nac = request.form.get("fecha_nacimiento")

        if not fecha_nac:
            return "Falta fecha de nacimiento"

        fecha_nac = datetime.strptime(fecha_nac, "%Y-%m-%d").date()

        hoy = date.today()

        edad = hoy.year - fecha_nac.year - (
            (hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day)
        )

        # 🔥 traer limites de edad
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
        SELECT edad_min, edad_max, validar_edad
        FROM distancias
        WHERE id = %s
        """, (distancia_id,))

        dist = cursor.fetchone()

        if not dist:
            cursor.close()
            conn.close()
            return "Error: distancia no encontrada"

        if dist.get("validar_edad"):

            edad_min = dist.get("edad_min")
            edad_max = dist.get("edad_max")

            if edad_min is not None and edad < edad_min:
                return f"""
                <div style="
                    max-width:420px;
                    margin:60px auto;
                    padding:25px;
                    border-radius:14px;
                    background:linear-gradient(135deg,#fff,#ffecec);
                    border:1px solid #ffb3b3;
                    text-align:center;
                    font-family:Arial;
                    box-shadow:0 10px 25px rgba(0,0,0,0.1);
                ">
                    <h2 style="color:#d32f2f;">🚫 Ups… no podés inscribirte</h2>

                    <p style="font-size:15px;color:#444;">
                        Esta distancia es para mayores de <b>{edad_min} años</b>.
                    </p>

                    <br>

                    <button onclick="window.history.back()" style="
                        padding:10px 20px;
                        border:none;
                        border-radius:8px;
                        background:#1976d2;
                        color:white;
                        font-weight:bold;
                        cursor:pointer;
                    ">
                        ← Volver
                    </button>
                </div>
                """

            if edad_max is not None and edad > edad_max:
                return f"""
                <div style="
                    max-width:420px;
                    margin:60px auto;
                    padding:25px;
                    border-radius:14px;
                    background:linear-gradient(135deg,#fff,#ffecec);
                    border:1px solid #ffb3b3;
                    text-align:center;
                    font-family:Arial;
                    box-shadow:0 10px 25px rgba(0,0,0,0.1);
                ">
                    <h2 style="color:#d32f2f;">🚫 Ups… no podés inscribirte</h2>

                    <p style="font-size:15px;color:#444;">
                        Esta distancia es hasta <b>{edad_max} años</b>.
                    </p>

                    <br>

                    <button onclick="window.history.back()" style="
                        padding:10px 20px;
                        border:none;
                        border-radius:8px;
                        background:#1976d2;
                        color:white;
                        font-weight:bold;
                        cursor:pointer;
                    ">
                        ← Volver
                    </button>
                </div>
                """

        cursor.close()
        conn.close() 

        
        remera = request.form.get("remera")
        
        persona_id = request.form["persona_id"]
        dni = request.form["dni"]

        import re

        dni = re.sub(r"\D", "", dni)  # deja solo números

        if len(dni) < 7 or len(dni) > 8:
            cursor.close()
            conn.close()
            return "<h2>DNI inválido (máximo 8 números)</h2>"
        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        email = request.form["email"]
        celular = request.form["celular"]

        fecha_nacimiento = request.form.get("fecha_nacimiento", "").strip()
        
        edad_evento = edad        

        edad_ingresada = request.form.get("edad", "").strip()

        if not fecha_nacimiento:
            cursor.close()
            conn.close()
            return "<h2>Debe ingresar la fecha de nacimiento.</h2>"

        genero = request.form["genero"]
        genero = genero.strip().upper()

        if genero not in ["M", "F", "X"]:
            genero = ""
        pais_id = request.form["pais_id"]

        provincia_id = request.form["provincia_id"]
        ciudad = request.form["ciudad"]
        instagram = request.form.get("instagram")
        strava = request.form.get("strava")
        facebook = request.form.get("facebook")
        
        team_id = request.form.get("team_id")
        team_nuevo = request.form.get("team_nuevo")

        if team_id == "":
            team_id = None

        talle_remera = request.form.get("remera")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
        SELECT incluye_remera
        FROM distancias
        WHERE id = %s
        """, (distancia_id,))

        datos = cursor.fetchone()

        if datos["incluye_remera"] == 0:
            talle_remera = None
              

            
        if edad_ingresada:

            if not edad_ingresada.isdigit():
                cursor.close()
                conn.close()
                return "<h2>La edad debe ser un número.</h2>"

            edad_real = date.today().year - int(fecha_nacimiento[:4])

            if abs(int(edad_ingresada) - edad_real) > 1:
                cursor.close()
                conn.close()

                return """
                <script>
                alert("La edad no coincide con la fecha de nacimiento");
                window.history.back();
                </script>
                """

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
    
        
        
        # crear team si es nuevo
        if team_nuevo:
            cursor.execute(
                "SELECT id FROM teams WHERE nombre = %s",
                (team_nuevo.upper(),)
            )

            team = cursor.fetchone()

            if team:
                team_id = team["id"]
            else:
                cursor.execute("""
                    INSERT INTO teams (nombre, activo, organizador_id)
                    VALUES (%s,1,1)
                """, (team_nuevo.upper(),))

                conn.commit()
                team_id = cursor.lastrowid

        # validar email
        email_confirmar = request.form["email_confirmar"]

        if email != email_confirmar:
            cursor.close()
            conn.close()
            return "<h2>Los emails no coinciden.</h2>"

        # crear persona si no existe
        cursor.execute("SELECT id FROM personas WHERE dni = %s", (dni,))
        persona_existente = cursor.fetchone()

        if not persona_existente:

            cursor.execute("""
            INSERT INTO personas
            (dni, nombre, apellido, email, celular, fecha_nac, genero, pais_id, provincia_id, ciudad, team_id, instagram, strava, facebook)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                dni,
                nombre.upper(),
                apellido.upper(),
                email,
                celular,
                fecha_nacimiento,
                genero,
                pais_id,
                provincia_id,
                ciudad.upper(),
                team_id,
                instagram,
                strava,
                facebook
            ))

            conn.commit()
            persona_id = cursor.lastrowid

        else:
            persona_id = persona_existente["id"]
            cursor.execute("""
            UPDATE personas
            SET nombre=%s,
                apellido=%s,
                email=%s,
                celular=%s,
                fecha_nac=%s,
                genero=%s,
                pais_id=%s,
                provincia_id=%s,
                ciudad=%s,
                team_id=%s,
                instagram=%s,
                strava=%s,
                facebook=%s
            WHERE id=%s
            """,(
                nombre.upper(),
                apellido.upper(),
                email,
                celular,
                fecha_nacimiento,
                genero,
                pais_id,
                provincia_id,
                ciudad.upper(),
                team_id,
                instagram,
                strava,
                facebook,
                persona_id
            ))

        conn.commit()

        # verificar inscripción previa
        cursor.execute("""
            SELECT id, estado_pago 
            FROM inscripciones
            WHERE evento_id=%s AND persona_id=%s
        """, (evento_id, persona_id))

        existe = cursor.fetchone()

        if existe:
            if existe["estado_pago"] in ["pagado", "aprobado"]:
                return "<h2>Ya estás inscripto y pagado en este evento.</h2>"

            if existe["estado_pago"] == "pendiente":
                return """
                <h2>Ya tenés una inscripción pendiente de pago.</h2>
                <p>Revisá tu email o intentá nuevamente más tarde.</p>
                """

       

        if existe:
            cursor.close()
            conn.close()
            return "<h2>Ya estás inscripto en este evento.</h2>"

        # verificar cupo
        cursor.execute("""
            SELECT cupo,
            (SELECT COUNT(*) FROM inscripciones
            WHERE distancia_id=%s AND evento_id=%s) AS inscriptos
            FROM distancias
            WHERE id=%s
        """, (distancia_id, evento_id, distancia_id))

        datos = cursor.fetchone()

        if datos["inscriptos"] >= datos["cupo"]:
            cursor.close()
            conn.close()
            return "<h2>Esta distancia ya completó el cupo.</h2>"

        # -----------------------------
        # validar fechas de inscripción
        # -----------------------------

        cursor.execute("""
        SELECT fecha_inicio_inscripcion, fecha_fin_inscripcion
        FROM distancias
        WHERE id = %s
        """, (distancia_id,))

        dist = cursor.fetchone()

        hoy = date.today()

        inicio = dist["fecha_inicio_inscripcion"]
        fin = dist["fecha_fin_inscripcion"]

        if inicio and hoy < inicio:
            cursor.close()
            conn.close()
            return layout("<h2>⏳ Las inscripciones aún no comenzaron</h2>")

        if fin and hoy > fin:
            cursor.close()
            conn.close()
            return layout("<h2>❌ Las inscripciones ya están cerradas</h2>")


        # -----------------------------
        # insertar inscripción
        # -----------------------------

        
        cursor.execute("""
        INSERT INTO inscripciones
        (evento_id, persona_id, distancia_id, edad_evento, email_contacto, telefono_contacto, estado_pago, talle_remera)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (evento_id, persona_id, distancia_id, edad_evento, email, celular, "pendiente", talle_remera))
        conn.commit()

        inscripcion_id = cursor.lastrowid
        numero = f"{evento_id}-{str(inscripcion_id).zfill(8)}"

        cursor.execute(
            "UPDATE inscripciones SET numero_inscripcion=%s WHERE id=%s",
            (numero, inscripcion_id)
        )

        conn.commit()

        # 🔥 OBTENER TOKEN DEL ORGANIZADOR
        cursor.execute("""
        SELECT o.access_token_mp
        FROM eventos e
        JOIN organizadores o ON e.organizador_id = o.id
        WHERE e.id = %s
        """, (evento_id,))

        organizador = cursor.fetchone()

        if not organizador or not organizador.get("access_token_mp"):
            return "Error: el organizador no tiene MercadoPago conectado"

        access_token = organizador["access_token_mp"]

        # 🔥 obtener precio
        cursor.execute("""
        SELECT precio
        FROM distancias
        WHERE id = %s
        """, (distancia_id,))

        dist = cursor.fetchone()
        precio = dist["precio"]

        comision = round(precio * 0.03, 2)
        precio_final = precio + comision

        # 🔥 crear pago
        sdk = mercadopago.SDK(access_token)

        preference_data = {
            "items": [
                {
                    "title": f"Inscripción {nombre_evento}",
                    "quantity": 1,
                    "unit_price": round(precio_final, 2)
                }
            ],
            "application_fee": round(comision, 2),
            "external_reference": str(inscripcion_id),
            "back_urls": {
                "success": f"{BASE_URL}/pago_exitoso",
                "failure": f"{BASE_URL}/pago_error",
                "pending": f"{BASE_URL}/pago_pendiente"
            },
            "auto_return": "approved"
        }

        preference = sdk.preference().create(preference_data)
        

        cursor.close()
        conn.close()
        return redirect(preference["response"]["init_point"])

        
                

@app.route("/evento/<int:evento_id>/panel")
def panel_evento(evento_id):
    if "organizador_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # -------------------
    # datos del evento
    # -------------------
    cursor.execute("""
    SELECT nombre, fecha, lugar, hora, organizador_id, estado, imagen, publicado
    FROM eventos
    WHERE id = %s
    """,(evento_id,))
    evento = cursor.fetchone()

    if not evento or evento["organizador_id"] != session["organizador_id"]:
        return "<h2>No tenés acceso a este evento</h2>"
    
    nombre_evento = evento["nombre"] if evento else "Evento"
    salida = f"""
    <h1>Panel del evento</h1>

    <div style="
    background:#f8f9fa;
    padding:12px;
    border-radius:6px;
    margin-bottom:15px;
    font-size:18px;
    border-left:5px solid #1976d2;
    ">
    🏁 <b>{nombre_evento}</b>
    </div>
    """

    
    # -------------------
    # total inscriptos
    # -------------------
    cursor.execute("""
    SELECT COUNT(*) AS total
    FROM inscripciones
    WHERE evento_id = %s
    """,(evento_id,))
    total_inscriptos = cursor.fetchone()["total"]

    # -------------------
    # distancias
    # -------------------
    cursor.execute("SELECT DATABASE()")
    print("DB PANEL:", cursor.fetchone())

    cursor.execute("SHOW COLUMNS FROM distancias")
    print("COLUMNAS PANEL:", cursor.fetchall())
    cursor.execute("""
    SELECT 
        d.id,
        d.nombre,
        d.cupo,
        d.precio,
        d.incluye_remera,
        d.es_gratis,
        d.fecha_inicio_inscripcion,
        d.fecha_fin_inscripcion,
        COUNT(i.id) AS inscriptos
    FROM distancias d
    LEFT JOIN inscripciones i 
        ON d.id = i.distancia_id
        AND i.evento_id = %s
    WHERE d.evento_id = %s
    AND d.activo = 1               
    GROUP BY d.id
    ORDER BY d.nombre
    """,(evento_id,evento_id))
    distancias = cursor.fetchall()

    # -------------------
    # 💰 pagos
    # -------------------
    cursor.execute("""
    SELECT 
        SUM(CASE WHEN p.estado = 'aprobado' THEN p.monto ELSE 0 END) as cobrado,
        SUM(CASE WHEN p.estado = 'pendiente' THEN p.monto ELSE 0 END) as pendiente,
        SUM(CASE WHEN p.estado = 'rechazado' THEN p.monto ELSE 0 END) as rechazado
    FROM pagos p
    JOIN inscripciones i ON p.inscripcion_id = i.id
    WHERE i.evento_id = %s
    """, (evento_id,))
    pagos = cursor.fetchone()

    cursor.execute("""
    SELECT SUM(d.precio) as esperado
    FROM inscripciones i
    JOIN distancias d ON d.id = i.distancia_id
    WHERE i.evento_id = %s
    AND d.es_gratis = 0
    """, (evento_id,))
    esperado = cursor.fetchone()["esperado"] or 0

    cobrado = pagos["cobrado"] or 0
    cursor.execute("""
    SELECT COUNT(*) as cantidad
    FROM inscripciones
    WHERE evento_id = %s
    AND estado_pago = 'pendiente'
    """, (evento_id,))

    pendientes_cantidad = cursor.fetchone()["cantidad"]
    pendiente = pendientes_cantidad
    rechazado = pagos["rechazado"] or 0
    total_pendientes = pendientes_cantidad
    cursor.execute("""
    SELECT COUNT(*) as total
    FROM inscripciones
    WHERE evento_id = %s
    AND estado_pago IN ('pagado','aprobado')
    """, (evento_id,))
    total_pagados = cursor.fetchone()["total"]
    if total_inscriptos > 0:
        porcentaje = int((total_pagados / total_inscriptos) * 100)
    else:
        porcentaje = 0

    cursor.close()
    conn.close()

    # -------------------
    # HEADER + CARDS
    # -------------------
    cobrado = cobrado or 0
    salida += f"""
    <div style="display:flex; gap:20px; margin-bottom:20px; flex-wrap:wrap;">

        <div style="background:#1976d2;color:white;padding:20px;border-radius:10px;width:200px;">
            <b>Total inscriptos</b>
            <h2>{total_inscriptos}</h2>
        </div>

        <div style="background:#4caf50;color:white;padding:20px;border-radius:10px;width:200px;">
            <b>Pagados</b>
            <h2>{total_pagados}</h2>
        </div>

        <div style="background:#ff9800;color:white;padding:20px;border-radius:10px;width:200px;">
            <b>Pendientes</b>
            <h2>{total_pendientes}</h2>
        </div>

        <div style="background:#616161;color:white;padding:20px;border-radius:10px;width:200px;">
            <b>💰 Cobrado</b>
            <h2>${"{:,.0f}".format(cobrado).replace(",", ".")}</h2>
        </div>

    </div>
    """

    # -------------------
    # BOTONES
    # -------------------
    
    estado_publicado = evento["publicado"]

    texto_publicar = "🟢 Publicado" if estado_publicado else "⚪ Publicar evento"

    salida += f"""
    <div style="display:flex; gap:5px; margin-bottom:20px">

    <a href="/evento/{evento_id}/toggle_publicado">
        <button class="btn">
        {texto_publicar}
        </button>
    </a>

    <button onclick="copiarLink({evento_id}, '{nombre_evento}')">
    🔗 Copiar link
    </button>

    <a href="/evento/{evento_id}/inscripciones">
        <button class="btn">🔴 Inscripciones</button>
    </a>

    <a href="/evento/{evento_id}/distancias">
        <button class="btn">➕ Nueva competencia</button>
    </a>

    <a href="/evento/{evento_id}/inscriptos">
        <button class="btn">👥 Ver inscriptos</button>
    </a>

    <a href="/evento/{evento_id}/editar">
        <button class="btn">✏️ Editar evento</button>
    </a>

    </div>
    """
    salida += r"""
    <script>
    function copiarLink(evento_id, nombre_evento) {

        const slug = nombre_evento
            .toLowerCase()
            .replace(/[^a-z0-9\s-]/g, "")
            .replace(/\s+/g, "-");

        const url = window.location.origin + "/evento/" + evento_id + "/" + slug;

        const temp = document.createElement("input");
        temp.value = url;
        document.body.appendChild(temp);
        temp.select();
        document.execCommand("copy");
        document.body.removeChild(temp);

        alert("Link copiado:\n" + url);
    }
    </script>
    """
    
    # -------------------
    # TABLA DISTANCIAS (NO BORRÉ)
    # -------------------
    if len(distancias) == 0:

        salida += "<p>Aún no hay competencias creadas.</p>"

    else:

        salida += "<table border='1' cellpadding='8'>"

        salida += """
        <tr>
            <th>Distancia</th>
            <th>Precio</th>
            <th>Cupo</th>
            <th>Inscriptos</th>
            <th>Disponibles</th>
            <th>%</th>
        </tr>
        """

        for d in distancias:

            disponibles = d["cupo"] - d["inscriptos"]
            porcentaje_d = int((d["inscriptos"] / d["cupo"]) * 100) if d["cupo"] > 0 else 0

            salida += f"""
            <tr>
                <td>
                    {d['nombre']}
                    <a href="/evento/{evento_id}/editar_distancia/{d['id']}" style="margin-left:8px; text-decoration:none;">
                        ✏️
                    </a>
                </td>
                <td>{"Gratis" if d['es_gratis'] else f"${d['precio'] or 0}"}</td>
                <td>{d['cupo']}</td>
                <td>{d['inscriptos']}</td>
                <td>{disponibles}</td>
                <td>{porcentaje_d}%</td>
            </tr>
            """

        salida += "</table>"
    

    organizador_id = session.get("organizador_id")

    cursor = get_db_connection().cursor(dictionary=True)

    conn2 = get_db_connection()
    cursor2 = conn2.cursor(dictionary=True)

    cursor2.execute("""
    SELECT id, nombre
    FROM eventos
    WHERE organizador_id = %s
    """, (organizador_id,))

    eventos = cursor2.fetchall()

    cursor2.close()
    conn2.close()
    return layout(salida, evento_id=evento_id, eventos=eventos)
    
@app.route("/evento/<int:evento_id>/editar_distancia/<int:distancia_id>", methods=["GET","POST"])
def editar_distancia(evento_id, distancia_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "GET":

        cursor.execute("""
        SELECT *
        FROM distancias
        WHERE id=%s
        """,(distancia_id,))

        d = cursor.fetchone()

        cursor.close()
        conn.close()

        salida = f"""
        <h1>Editar competencia</h1>

        <form method="POST">

        Nombre<br>
        <input type="text" name="nombre" value="{d['nombre']}"><br><br>

        Cupo<br>
        <input type="number" name="cupo" value="{d['cupo']}"><br><br>

        Precio<br>
        <input type="number" name="precio" value="{d['precio']}"><br><br>

        Inicio inscripción<br>
        <input type="date" name="inicio" value="{d['fecha_inicio_inscripcion'].strftime('%Y-%m-%d') if d['fecha_inicio_inscripcion'] else ''}"<br><br>

        Fin inscripción<br>
        <input type="date" name="fin" value="{d['fecha_fin_inscripcion'].strftime('%Y-%m-%d') if d['fecha_fin_inscripcion'] else ''}"<br><br>

        <label><b>Incluye remera</b></label><br>
        <select name="remera" style="margin-bottom:15px;">
            <option value="0" {"selected" if d['incluye_remera']==0 else ""}>No</option>
            <option value="1" {"selected" if d['incluye_remera']==1 else ""}>Sí</option>
        </select>

        <br>

        <label><b>Es gratis</b></label><br>
        <select name="gratis">
            <option value="0" {"selected" if d['es_gratis']==0 else ""}>No</option>
            <option value="1" {"selected" if d['es_gratis']==1 else ""}>Sí</option>
        </select>
        <br>
        <br><br>

        <label><b>Validar edad</b></label><br>
        <input type="checkbox" name="validar_edad" value="1"
        {"checked" if d.get("validar_edad") else ""}>

        <br><br>

        Edad mínima<br>
        <input type="number" name="edad_min" value="{d.get('edad_min') or ''}"><br><br>

        Edad máxima<br>
        <input type="number" name="edad_max" value="{d.get('edad_max') or ''}"><br><br>
                <br>
                <button type="submit">Guardar</button>

                </form>
                """

        return layout(salida)

    # POST

    nombre = request.form["nombre"]
    cupo = request.form["cupo"]
    precio = request.form["precio"]
    inicio = request.form["inicio"]
    fin = request.form["fin"]
    remera = request.form["remera"]
    gratis = request.form["gratis"]
    validar_edad = request.form.get("validar_edad")
    edad_min = request.form.get("edad_min")
    edad_max = request.form.get("edad_max")

    validar_edad = 1 if validar_edad else 0

    if not validar_edad:
        edad_min = None
        edad_max = None

    cursor.execute("""
    UPDATE distancias
    SET nombre=%s,
        cupo=%s,
        precio=%s,
        fecha_inicio_inscripcion=%s,
        fecha_fin_inscripcion=%s,
        incluye_remera=%s,
        es_gratis=%s,
        validar_edad=%s,
        edad_min=%s,
        edad_max=%s
    WHERE id=%s
    """,(nombre,cupo,precio,inicio,fin,remera,gratis,validar_edad,edad_min,edad_max,distancia_id))

    conn.commit()

    cursor.close()
    conn.close()

    return f"""
    <script>
    window.location.href="/evento/{evento_id}/panel"
    </script>
    """

@app.route("/evento/<int:evento_id>/eliminar_distancia/<int:distancia_id>")
def eliminar_distancia(evento_id, distancia_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # verificar si hay inscriptos
    cursor.execute("""
    SELECT COUNT(*) AS total
    FROM inscripciones
    WHERE distancia_id=%s
    """,(distancia_id,))
    inscriptos = cursor.fetchone()["total"]

    
    # 💰 total recaudado
    cursor.execute("""
    SELECT SUM(p.monto) as total
    FROM pagos p
    JOIN inscripciones i ON p.inscripcion_id = i.id
    WHERE i.evento_id = %s
    AND p.estado = 'aprobado'
    """, (evento_id,))
    recaudado = cursor.fetchone()["total"] or 0

    if inscriptos > 0 or recaudado > 0:
    

        cursor.close()
        conn.close()

        return f"""
        <script>
        alert("No se puede eliminar porque tiene inscriptos.");
        window.location.href="/evento/{evento_id}/panel"
        </script>
        """

    # eliminar distancia
    cursor.execute(
        "DELETE FROM distancias WHERE id=%s",
        (distancia_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return f"""
    <script>
    window.location.href="/evento/{evento_id}/panel"
    </script>
    """


    return layout(salida)

@app.route("/organizador/editar_evento/<int:evento_id>", methods=["GET", "POST"])
def editar_evento(evento_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # traer evento actual
    cursor.execute("SELECT * FROM eventos WHERE id = %s", (evento_id,))
    evento = cursor.fetchone()

    if request.method == "POST":

        nombre = request.form["nombre"]
        fecha = request.form["fecha"]
        hora = request.form["hora"]
        lugar = request.form["lugar"]
        provincia = request.form["provincia"]
        direccion = request.form["direccion"]
        latitud = request.form.get("latitud")
        longitud = request.form.get("longitud")

        latitud = float(latitud) if latitud else None
        longitud = float(longitud) if longitud else None

        cursor.execute("""
            UPDATE eventos
            SET nombre=%s, fecha=%s, hora=%s,
                lugar=%s, provincia=%s,
                direccion=%s, latitud=%s, longitud=%s
            WHERE id=%s
        """, (nombre, fecha, hora, lugar, provincia,
              direccion, latitud, longitud, evento_id))

        conn.commit()
        conn.close()

        return redirect(f"/evento/{evento_id}")

    conn.close()

    return render_template("editar_evento.html", evento=evento)

@app.route("/evento/<int:evento_id>/toggle_publicado")
def toggle_publicado(evento_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE eventos
        SET publicado = NOT publicado
        WHERE id = %s
    """, (evento_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return f"""
    <script>
    window.location.href="/evento/{evento_id}/panel"
    </script>
    """
@app.route("/webhook_mp", methods=["POST"])
def webhook_mp():
    data = request.json
    print("WEBHOOK:", data)

    # 1. Obtener payment_id
    payment_id = data.get("data", {}).get("id")

    if not payment_id:
        return "NO PAYMENT ID", 200

    # 2. Consultar a MercadoPago
    payment = sdk.payment().get(payment_id)
    payment_info = payment["response"]

    print("PAYMENT INFO:", payment_info)

    # 3. Verificar estado
    if payment_info.get("status") == "approved":

        inscripcion_id = payment_info.get("external_reference")

        print("INSCRIPCION A ACTUALIZAR:", inscripcion_id)

        # 4. Actualizar DB
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE inscripciones
            SET estado_pago = 'pagado',
                acreditado = 1,
                payment_id = %s
            WHERE id = %s
        """, (payment_id, inscripcion_id))

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ INSCRIPCION MARCADA COMO PAGADA")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)