from flask import Flask, request
from db import get_db_connection
from datetime import date

app = Flask(__name__)
app.secret_key = "12356"
from routes.organizador import organizador_bp
from routes.eventos import eventos_bp
from flask import session, redirect
import re
from db import get_db_connection
def slugify(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-z0-9\s-]', '', texto)
    texto = texto.replace(" ", "-")
    return texto

app.register_blueprint(organizador_bp)
app.register_blueprint(eventos_bp)

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
   
    salida = f"""
    <div style="max-width:900px;margin:auto;margin-top:30px">

    <div style="
    display:flex;
    gap:20px;
    align-items:stretch;
    ">

    <div style="flex:1">

    <img src="/static/eventos/{imagen}"
    style="
    width:100%;
    height:320px;
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

    <div style="
    display:flex;
    justify-content:center;
    gap:20px;
    margin-top:10px;
    font-size:18px;
    ">

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


            # calcular inscriptos y disponibles
            cursor2 = conn.cursor(dictionary=True)
            cursor2.execute("""
                SELECT COUNT(*) as inscriptos
                FROM inscripciones
                WHERE distancia_id=%s AND evento_id=%s
            """, (d["id"], evento_id))

            data = cursor2.fetchone()
            inscriptos = data["inscriptos"]
            disponibles = max(d["cupo"] - inscriptos, 0)

            cursor2.close()


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
        <h1>Inscripción {nombre_evento}</h1>
        <form method="POST">

            <input type="hidden" name="distancia_id" value="{distancia_id}">
            <input type="text" name="dni" maxlength="8"  
            oninput="this.value=this.value.replace(/[^0-9]/g,'')" required>
            <button type="submit" name="accion" value="buscar">Continuar</button>
        </form>
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

        salida = "<h2>Datos del corredor</h2>"
        salida += "<form method='POST'>"

       
        salida += f"<input type='hidden' name='distancia_id' value='{distancia_id}'>"
        salida += f"<h3>Distancia: {distancia['nombre']}</h3>"

        salida += "<h3>Identificación</h3>"
        salida += f"DNI: <input type='text' name='dni' value='{dni}' pattern='[0-9]{{7,8}}' maxlength='8' required><br>"

        salida += "<input type='hidden' name='accion' value='confirmar'>"
        salida += f"<input type='hidden' name='persona_id' value='{persona['id']}'>"
        salida += f"Nombre: <input type='text' name='nombre' value='{persona['nombre']}'><br>"
        salida += f"Apellido: <input type='text' name='apellido' value='{persona['apellido']}'><br>"
        salida += f"Email: <input type='email' name='email' value='{persona['email']}' style='width:300px' required><br>"
        salida += "Confirmar email: <input type='email' name='email_confirmar' style='width:300px' required><br>"
        salida += f"Celular: <input type='text' name='celular' value='{persona['celular']}'><br>"

        salida += f"Fecha nacimiento: <input type='date' name='fecha_nacimiento' value='{persona.get('fecha_nac','')}' required><br>"
        salida += "Edad: <input type='number' name='edad' min='1' max='100'><br>"

        salida += f"""
Género:<br>
<select name='genero'>
    <option value=''>Seleccionar</option>
    <option value='M' {"selected" if persona.get("genero")=="M" else ""}>Masculino</option>
    <option value='F' {"selected" if persona.get("genero")=="F" else ""}>Femenino</option>
    <option value='X' {"selected" if persona.get("genero")=="X" else ""}>Otro</option>
</select><br>
"""

        salida += "País:<br>"
        salida += "<select name='pais_id'>"

        for p in paises:
            selected = ""
            if persona.get("pais_id") == p["id"]:
                selected = "selected"

            salida += f"<option value='{p['id']}' {selected}>{p['nombre']}</option>"

        salida += "</select><br>"
        salida += "Provincia:<br>"
        salida += "<select name='provincia_id'>"

        for p in provincias:
            selected = ""
            if persona.get("provincia_id") == p["id"]:
                selected = "selected"

            salida += f"<option value='{p['id']}' {selected}>{p['nombre']}</option>"
 
        salida += "</select><br>"
        salida += f"ciudad: <input type='text' name='ciudad' value='{persona['ciudad']}'><br>"

        salida += f"Instagram: <input type='text' name='instagram'><br>"
        salida += f"Strava: <input type='text' name='strava'><br>"
        salida += f"Facebook: <input type='text' name='facebook'><br>"

        # 👇 ACÁ VA
        if str(distancia.get("incluye_remera")) == "1":
            salida += """
            <br>
            <b>Talle de remera</b><br>
            <select name="remera" required>
                <option value="">Seleccionar</option>
                <option>XS</option>
                <option>S</option>
                <option>M</option>
                <option>L</option>
                <option>XL</option>
                <option>XXL</option>
            </select><br><br>
            """

        salida += "Team existente:<br>"
        salida += "<select name='team_id'>"
        salida += "<option value=''>-- Sin equipo --</option>"

        for t in teams:
            salida += f"<option value='{t['id']}'>{t['nombre']}</option>"

        salida += "</select><br><br>"

        salida += "O escribir nuevo team:<br>"
        salida += "<input type='text' name='team_nuevo'><br>"
      
                
        salida += "<button type='submit'>Confirmar inscripción</button>"
        salida += "</form>"

        return salida

    # --------------------------------------
    # CONFIRMAR INSCRIPCIÓN
    # --------------------------------------
    
    if accion == "confirmar":

        remera = request.form.get("remera")
        distancia_id = request.form["distancia_id"]

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
        
        edad_evento = None

        if fecha_nacimiento:
            edad_evento = date.today().year - int(fecha_nacimiento[:4])
        

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
        if persona_id == "":

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
            SELECT id FROM inscripciones
            WHERE evento_id=%s AND persona_id=%s
        """, (evento_id, persona_id))

        existe = cursor.fetchone()

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

        cursor.close()
        conn.close()

        return f"""
        <h2>Inscripción confirmada</h2>
        <p>Número: {numero}</p>
        <a href="/evento/{evento_id}">
            <button>Volver al evento</button>
        </a>
        """       


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
    AND estado_pago = 'pagado'
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
   
    <div style="display:flex; gap:20px; margin-bottom:20px;">

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
            <div style="background:#616161;color:white;padding:20px;border-radius:10px;width:200px;">
            <b>💰 Cobrado</b>
            <h2>${cobrado:,.0f}</h2>
        </div>
            
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

    cursor.execute("""
    UPDATE distancias
    SET nombre=%s,
        cupo=%s,
        precio=%s,
        fecha_inicio_inscripcion=%s,
        fecha_fin_inscripcion=%s,
        incluye_remera=%s,
        es_gratis=%s
    WHERE id=%s
    """,(nombre,cupo,precio,inicio,fin,remera,gratis,distancia_id))

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
@app.route("/test-db")
def test_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SHOW TABLES;")
    tablas = cursor.fetchall()

    cursor.close()
    conn.close()

    return str(tablas)

if __name__ == "__main__":
    app.run(debug=True)