from flask import Blueprint, request, jsonify, redirect
from db import get_db_connection
from layout import layout
import os
from werkzeug.utils import secure_filename
from PIL import Image
from flask import send_file
from openpyxl import Workbook
import io

organizador_bp = Blueprint("organizador", __name__)


@organizador_bp.route("/evento/<int:evento_id>/inscriptos")
def ver_inscriptos(evento_id):
    tab = request.args.get("tab") or "resumen"

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------------------------
    # Total general del evento
    # ---------------------------
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM inscripciones
        WHERE evento_id = %s
    """, (evento_id,))
    total_evento = cursor.fetchone()["total"]

    # ---------------------------
    # Totales por distancia
    # ---------------------------
    cursor.execute("""
    SELECT 
        d.id,
        d.nombre,
        d.cupo,

        COUNT(i.id) AS total,

        SUM(CASE WHEN i.estado_pago = 'pagado' THEN 1 ELSE 0 END) AS pagados,
        SUM(CASE WHEN i.estado_pago = 'pendiente' THEN 1 ELSE 0 END) AS pendientes,
        SUM(CASE WHEN i.estado_pago = 'vencido' THEN 1 ELSE 0 END) AS vencidos

    FROM distancias d

    LEFT JOIN inscripciones i
        ON d.id = i.distancia_id
        AND i.evento_id = %s

    WHERE d.evento_id = %s
    AND d.activo = 1
                   
    GROUP BY d.id
    """, (evento_id, evento_id))

    distancias = cursor.fetchall()
    
    
    # ---------------------------
    # Listado completo
    # ---------------------------

    cursor.execute("""
        SELECT
            i.numero_inscripcion,
            i.fecha_inscripcion,
            i.dorsal,
            p.nombre,
            p.apellido,
            p.dni,
            p.fecha_nac,
            d.nombre AS distancia,
            p.email,
            p.celular,
            i.estado_pago,
            t.nombre AS team
        FROM inscripciones i
        JOIN personas p ON p.id = i.persona_id
        JOIN distancias d ON d.id = i.distancia_id
        LEFT JOIN teams t ON p.team_id = t.id
        WHERE i.evento_id = %s
        ORDER BY i.fecha_inscripcion DESC
    """, (evento_id,))

    inscriptos = cursor.fetchall()

    cursor.close()
    conn.close()

    salida = f"""
    <a href="/evento/{evento_id}/panel" style="
    display:inline-block;
    margin-bottom:15px;
    padding:8px 15px;
    background:#1976d2;
    color:white;
    border-radius:6px;
    text-decoration:none;
    ">
    ← Volver al panel
    </a>

    <h1>Inscriptos del evento</h1>
    """

    # -------------------
    # RESUMEN
    # -------------------

    salida += f"""
    

    <input type="hidden" name="tab" id="tab_actual" value="{tab}">

    <div id="resumen" style="display:none">
    """
    
    salida += "<div style='display:flex;gap:20px;flex-wrap:wrap;margin-bottom:30px'>"

    for d in distancias:

        salida += f"""
        <div style='
        background:#f5f5f5;
        padding:15px;
        border-radius:10px;
        width:220px;
        border-left:6px solid #1976d2a
        '>
        <b>{d['nombre']}</b><br><br>

        Total: {"{:,.0f}".format(d['total']).replace(",", ".")}<br>
        <span style='color:green'>Pagados: {d['pagados']}</span><br>
        <span style='color:orange'>Pendientes: {d['pendientes']}</span><br>
        <span style='color:red'>Vencidos: {d['vencidos']}</span>

        </div>
        """

    salida += "</div>"

    salida += """
    <div style="margin-bottom:10px">

    <input type="text" id="buscar"
    placeholder="Buscar por nombre, DNI o email..."
    style="
    padding:8px;
    width:350px;
    border:1px solid #ccc;
    border-radius:6px
    ">

    </div>
    """

    # -----------------------
    # TABLA INSCRIPTOS
    # -----------------------
    salida += "<h2>Listado de inscriptos</h2>"

    salida += """
    <div style="
    max-height:60vh;
    overflow-y:auto;
    border:1px solid #ccc;
    border-radius:6px
    ">

    <table id="tabla_inscriptos"
    style="
    border-collapse:collapse;
    width:100%;
    font-size:13px
    " border="1" cellpadding="6">
    """

    salida += """
    <tr style="background:#eee">
    <th>Código</th>
    <th>Fecha</th>
    <th>Nombre</th>
    <th>Email</th>
    <th>Documento</th>
    <th>Edad</th>
    <th>Competición</th>
    <th>Team</th>
    <th>Número</th>
    <th>Estado</th>
    <th>Editar</th>
    </tr>
    """
    

    for ins in inscriptos:
        print("TEAM RAW:", ins.get("team"))
        # 🔥 LIMPIAR TEAM PRIMERO
        team = ins.get("team")

        if team:
            team = team.strip()
            if team.lower() == "none" or team == "":
                team = "Sin equipo"
        else:
            team = "Sin equipo"

        # resto de lógica
        edad = "-"

        if ins["fecha_nac"]:
            from datetime import date
            edad = date.today().year - ins["fecha_nac"].year 

        estado_db = ins["estado_pago"]

        if estado_db == "pagado":
            estado = "<span style='background:#4caf50;color:white;padding:4px 8px;border-radius:4px'>Pagado</span>"
        elif estado_db == "pendiente":
            estado = "<span style='background:#ff9800;color:white;padding:4px 8px;border-radius:4px'>Pendiente</span>"
        elif estado_db == "vencido":
            estado = "<span style='background:#f44336;color:white;padding:4px 8px;border-radius:4px'>Vencido</span>"
        else:
            estado = estado_db

        fecha = ins["fecha_inscripcion"].strftime("%d/%m/%Y %H:%M")

        # 👇 RECIÉN ACÁ LO USÁS
        salida += f"""
        <tr>
        <td>{ins['numero_inscripcion']}</td>
        <td>{fecha}</td>
        <td>{ins['nombre']} {ins['apellido']}</td>
        <td>{ins['email']}</td>
        <td>{ins['dni']}</td>
        <td>{edad}</td>
        <td>{ins['distancia']}</td>
        <td>{team}</td>
        <td>{ins['dorsal'] if ins['dorsal'] else '-'}</td>
        <td>{estado}</td>
        <td>
        <a href="/inscripcion/{ins['numero_inscripcion']}">
        <button type="button">✏️</button>
        </a>
        </td>
        </tr>
        """

    salida += "</table></div>"

    

    salida += """
    <script>

    document.getElementById("buscar").addEventListener("keyup", function(){

        let filtro = this.value.toLowerCase()

        let filas = document.querySelectorAll("#tabla_inscriptos tr")

        filas.forEach(function(fila, index){

            if(index === 0) return   // salta el encabezado

            let texto = fila.innerText.toLowerCase()

            if(texto.includes(filtro)){
                fila.style.display = ""
            } else {
                fila.style.display = "none"
            }

        })

    })

    </script>
    """
    salida += f"""
    <script>

    function mostrar(seccion) {{

        let resumen = document.getElementById("resumen");

        if(resumen) resumen.style.display = "none";

        if(seccion === "resumen") {{
            if(resumen) resumen.style.display = "block";
        }}
    }}

    window.onload = function() {{
        mostrar("{tab}");
    }}

    </script>
    """     
    
    return layout(salida)
@organizador_bp.route("/corredores")
def ver_corredores():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            p.id,
            p.nombre,
            p.apellido,
            p.dni,
            p.email,
            p.celular,
            p.ciudad,
            t.nombre AS team
        FROM personas p
        LEFT JOIN teams t ON p.team_id = t.id
        ORDER BY p.apellido, p.nombre
    """)

    corredores = cursor.fetchall()

    cursor.close()
    conn.close()

    salida = "<h1>Corredores registrados</h1>"

    salida += """
    <input type="text" id="buscar" placeholder="Buscar corredor..."
    style="width:300px;padding:6px;margin-bottom:10px">
    """

    salida += """
    <table border="1" cellpadding="6" style="border-collapse:collapse;width:100%" id="tabla_corredores">
    <thead>
    <tr style="background:#eee">
        <th>ID</th>
        <th>Nombre</th>
        <th>Apellido</th>
        <th>DNI</th>
        <th>Email</th>
        <th>Celular</th>
        <th>Ciudad</th>
        <th>Team</th>
        <th>Editar</th>
    </tr>
    </thead>
    <tbody>
    """

    for c in corredores:

        salida += f"""
        <tr>
            <td>{c['id']}</td>
            <td>{c['nombre']}</td>
            <td>{c['apellido']}</td>
            <td>{c['dni']}</td>
            <td>{c['email']}</td>
            <td>{c['celular']}</td>
            <td>{c['ciudad']}</td>
            <td>{c['team'] if c['team'] and c['team'] != 'None' else 'Sin equipo'}</td>
            <td>
            <a href="/corredor/{c['id']}">
            <button>✏️</button>
            </a>
            </td>
        </tr>
        """

    salida += "</tbody></table>"

    salida += """
    <script>

    document.getElementById("buscar").addEventListener("keyup", function(){

        let filtro = this.value.toLowerCase()
        let filas = document.querySelectorAll("#tabla_corredores tbody tr")

        filas.forEach(fila => {

            let texto = fila.innerText.toLowerCase()

            fila.style.display = texto.includes(filtro) ? "" : "none"

        })

    })

    </script>
    """

    return layout(salida)

@organizador_bp.route("/corredor/<int:persona_id>")
def ver_corredor(persona_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # datos del corredor
    cursor.execute("""
    SELECT *
    FROM personas
    WHERE id = %s
    """,(persona_id,))

    corredor = cursor.fetchone()

    if not corredor:
        cursor.close()
        conn.close()
        return layout("<h2>Corredor no encontrado</h2>")

    # inscripciones del corredor
    cursor.execute("""
    SELECT 
        i.id,
        i.numero_inscripcion,
        i.estado_pago,
        d.nombre AS distancia,
        e.nombre AS evento
    FROM inscripciones i
    JOIN distancias d ON i.distancia_id = d.id
    JOIN eventos e ON i.evento_id = e.id
    WHERE i.persona_id = %s
    """,(persona_id,))

    inscripciones = cursor.fetchall()

    cursor.close()
    conn.close()

    salida = f"<h1>{corredor['nombre']} {corredor['apellido']}</h1>"

    salida += "<h2>Inscripciones</h2>"

    salida += "<table border=1 cellpadding=6>"
    salida += """
    <tr>
        <th>Evento</th>
        <th>Distancia</th>
        <th>Estado</th>
    </tr>
    """

    for i in inscripciones:

        salida += f"""
        <tr>
            <td>{i['evento']}</td>
            <td>{i['distancia']}</td>
            <td>{i['estado_pago']}</td>
        </tr>
        """

    salida += "</table>"

    return layout(salida)

@organizador_bp.route("/organizador")
def panel_organizador():
    from flask import request, session
    if "organizador_id" not in session:
        return redirect("/login")

    organizador_id = session.get("organizador_id")
    evento_id = request.args.get("evento_id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, nombre, fecha, lugar, imagen
        FROM eventos
        WHERE activo = 1 AND organizador_id = %s
        ORDER BY fecha
    """, (organizador_id,))        

    eventos = cursor.fetchall()

    cursor.close()
    conn.close()
    
    mensaje = ""

    if request.args.get("ok") == "evento_creado":
        mensaje = """
        <div style="
            background:#d4edda;
            color:#155724;
            padding:10px;
            border-radius:5px;
            margin-bottom:15px;
        ">
            ✅ Evento creado correctamente
        </div>
        """
    
  
    salida = mensaje + f"""
    <h1>Panel del organizador</h1>
    """

    salida += """
    <a href="/organizador/nuevo_evento">
    <button style='padding:10px 15px;margin-bottom:20px'>
    ➕ Nuevo evento
    </button>
    </a>
    """

    salida += "<h2>Eventos activos</h2>"

    salida += """
    <div style='
        display:flex;
        flex-wrap:wrap;
        gap:25px;
        justify-content:flex-start;
    '>
    """

    for e in eventos:

        imagen = f"/static/eventos/{e['imagen']}" if e["imagen"] else "/static/logo.png"

        salida += f"""
        <div style="
            width:300px;
            background:#f8f8f8;
            border-radius:12px;
            overflow:hidden;
            box-shadow:0 4px 10px rgba(0,0,0,0.15);
            display:flex;
            flex-direction:column;
        ">

            <img src="{imagen}" style="
                width:100%;
                height:180px;
                object-fit:cover;
            ">

            <div style="padding:15px; display:flex; flex-direction:column; flex-grow:1;">

                <b style="font-size:18px; margin-bottom:8px;">
                    {e['nombre']}
                </b>

                <div style="font-size:14px; color:#555;">
                    📅 {e['fecha']}<br>
                    📍 {e['lugar']}
                </div>

                <div style="margin-top:auto; text-align:center;">
                    <a href="/evento/{e['id']}/panel">
                        <button style="
                            margin-top:15px;
                            padding:10px;
                            width:100%;
                            background:#222;
                            color:white;
                            border:none;
                            border-radius:6px;
                            cursor:pointer;
                        ">
                            Entrar al panel
                        </button>
                    </a>
                </div>

            </div>

        </div>
        """

    salida += "</div>"

  

    return layout(salida, evento_id=evento_id, eventos=eventos)

@organizador_bp.route("/organizador/nuevo_evento", methods=["GET","POST"])
def nuevo_evento():

    from flask import session, redirect

    # 🔐 PROTEGER RUTA
    if "organizador_id" not in session:
        return redirect("/login")
    salida = ""

    if request.method == "GET":

        salida += """
    <h1>Crear nuevo evento</h1>

    <form method="POST" enctype="multipart/form-data">

    Nombre del evento<br>
    <input type="text" name="nombre" style="width:350px" required>

    <br><br>

    Fecha<br>
    <input type="date" name="fecha" required>

    <br><br>

    Hora<br>
    <input type="time" name="hora">

    <br><br>

    Lugar<br>
    <input type="text" name="lugar" style="width:350px" required>

    <br><br>

    Provincia<br>
    <input type="text" name="provincia" style="width:350px">

    <br><br>

    Flyer del evento<br>
    <input type="file" name="imagen" accept="image/*" onchange="previewImagen(event)">

    <br><br>

    <img id="preview" style="max-width:400px;display:none;border-radius:8px">
    <small>Imagen promocional de la carrera</small>

    <br><br>

    <h3>📄 Documentos del evento</h3>

    <label>
    <input type="checkbox" name="reglamento_activo" value="1">
    Activar Reglamento
    </label>
    <br>
    <input type="file" name="reglamento_archivo" accept=".pdf,.txt">

    <br><br>

    <label>
    <input type="checkbox" name="deslinde_activo" value="1">
    Activar Deslinde
    </label>
    <br>
    <input type="file" name="deslinde_archivo" accept=".pdf,.txt">

    <br><br>

    <button type="submit">Crear evento</button>

    </form>

    <script>
    function previewImagen(event){

        let reader = new FileReader()

        reader.onload = function(){

            let img = document.getElementById("preview")

            img.src = reader.result
            img.style.display = "block"

        }

        reader.readAsDataURL(event.target.files[0])
    }
    </script>
    """
        return layout(salida)

    # --------- cuando se envía el formulario ---------

    nombre = request.form["nombre"]
    fecha = request.form["fecha"]
    hora = request.form["hora"]
    lugar = request.form["lugar"]
    provincia = request.form["provincia"]

    # -------- subir mapa --------

    archivo = request.files.get("imagen")
    imagen = None

    # -------- documentos --------

    reglamento_activo = 1 if request.form.get("reglamento_activo") else 0
    deslinde_activo = 1 if request.form.get("deslinde_activo") else 0

    reglamento_archivo = None
    deslinde_archivo = None

    carpeta_docs = "static/documentos"

    if not os.path.exists(carpeta_docs):
        os.makedirs(carpeta_docs)

    doc1 = request.files.get("reglamento_archivo")
    if doc1 and doc1.filename != "":
        reglamento_archivo = secure_filename(doc1.filename)
        doc1.save(os.path.join(carpeta_docs, reglamento_archivo))

    doc2 = request.files.get("deslinde_archivo")
    if doc2 and doc2.filename != "":
        deslinde_archivo = secure_filename(doc2.filename)
        doc2.save(os.path.join(carpeta_docs, deslinde_archivo))

    if archivo and archivo.filename != "":
        imagen = secure_filename(archivo.filename)

        carpeta = "static/eventos"

        if not os.path.exists(carpeta):
            os.makedirs(carpeta)

        ruta = os.path.join(carpeta, imagen)

        img = Image.open(archivo)
        img.thumbnail((1200,600))
        img.save(ruta)

    # -------- guardar evento --------

    conn = get_db_connection()
    cursor = conn.cursor()
    
    from flask import session
    organizador_id = session["organizador_id"]

    cursor.execute("""
    INSERT INTO eventos
    (
    nombre,
    fecha,
    hora,
    lugar,
    provincia,
    imagen,
    organizador_id,
    estado,
    activo,
    reglamento_activo,
    reglamento_archivo,
    deslinde_activo,
    deslinde_archivo
    )
    VALUES
    (%s,%s,%s,%s,%s,%s,%s,'cerrado',1,%s,%s,%s,%s)
    """, (
    nombre,
    fecha,
    hora,
    lugar,
    provincia,
    imagen,
    organizador_id,
    reglamento_activo,
    reglamento_archivo,
    deslinde_activo,
    deslinde_archivo
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/organizador?ok=evento_creado")
    
@organizador_bp.route("/evento/<int:evento_id>/toggle_inscripciones")
def toggle_inscripciones(evento_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ver estado actual
    cursor.execute("SELECT estado FROM eventos WHERE id = %s", (evento_id,))
    evento = cursor.fetchone()

    if evento["estado"] == "abierto":
        nuevo_estado = "cerrado"
    else:
        nuevo_estado = "abierto"

    cursor.execute(
        "UPDATE eventos SET estado = %s WHERE id = %s",
        (nuevo_estado, evento_id)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return f"""
    <script>
    window.location.href="/evento/{evento_id}/panel"
    </script>
    """
@organizador_bp.route("/evento/<int:evento_id>/distancias", methods=["GET","POST"])
def administrar_distancias(evento_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------- crear distancia ----------
    if request.method == "POST":

        accion = request.form.get("accion")

        # ELIMINAR
        if accion == "eliminar":
            distancia_id = request.form.get("distancia_id")

            cursor.execute("""
                UPDATE distancias
                SET activo = 0
                WHERE id = %s AND evento_id = %s
            """, (distancia_id, evento_id))

            conn.commit()
            return redirect(request.url)

        # CREAR
        nombre = request.form.get("nombre")
        cupo = request.form.get("cupo", 200)
        precio = request.form.get("precio", 0)

        fecha_inicio = request.form.get("fecha_inicio")
        fecha_fin = request.form.get("fecha_fin")

        incluye_remera = int(request.form.get("incluye_remera", 0))
        es_gratis = int(request.form.get("es_gratis", 0))
        validar_edad = 1 if request.form.get("validar_edad") else 0
        edad_min = request.form.get("edad_min")
        edad_max = request.form.get("edad_max")

        if not validar_edad:
            edad_min = None
            edad_max = None

        if not nombre:
            return "Error: falta nombre"

        # ✅ INSERT REAL
        cursor.execute("""
        INSERT INTO distancias
        (evento_id, nombre, cupo, precio,
        fecha_inicio_inscripcion,
        fecha_fin_inscripcion,
        incluye_remera,
        es_gratis,
        validar_edad,
        edad_min,
        edad_max)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            evento_id,
            nombre,
            cupo,
            precio,
            fecha_inicio,
            fecha_fin,
            incluye_remera,
            es_gratis,
            validar_edad,
            edad_min,
            edad_max
        ))

        conn.commit()

        return redirect(request.url)
    
        
    # ---------- listar distancias ----------
    cursor.execute("""
        SELECT id, nombre, cupo, precio
        FROM distancias
        WHERE evento_id = %s
        AND activo = 1
        ORDER BY id
    """, (evento_id,))

    distancias = cursor.fetchall()

    cursor.close()
    conn.close()
    
          
    salida = "<h1>Distancias del evento</h1>"

    salida += """
    <form method="POST">

    Nombre<br>
    <input type="text" name="nombre" placeholder="10K competitiva" required><br><br>

    Cupo<br>
    <input type="number" name="cupo" value="200"><br><br>

    Precio<br>
    <input type="number" id="precio" name="precio" value="0"><br><br>

    Inicio inscripción<br>
    <input type="date" name="fecha_inicio"><br><br>

    Fin inscripción<br>
    <input type="date" name="fecha_fin"><br><br>

    Incluye remera<br>
    <select name="incluye_remera">
        <option value="0">No</option>
        <option value="1">Sí</option>
    </select><br><br>

    ¿Es gratis?<br>
    <select name="es_gratis" id="gratis">
        <option value="0">No</option>
        <option value="1">Sí</option>
    </select><br><br>
    <br><br>

    <label><b>Validar edad</b></label><br>
    <input type="checkbox" name="validar_edad" value="1">

    <br><br>

    Edad mínima<br>
    <input type="number" name="edad_min"><br><br>

    Edad máxima<br>
    <input type="number" name="edad_max"><br><br>

    <button type="submit">Agregar competencia</button>

    </form>

    <script>

    function controlarPrecio(){

        let gratis = document.getElementById("gratis")
        let precio = document.getElementById("precio")

        if(gratis.value == "1"){
            precio.value = 0
            precio.disabled = true
        }else{
            precio.disabled = false
        }

    }

    document.getElementById("gratis").addEventListener("change", controlarPrecio)

    window.onload = controlarPrecio

    </script>
    """

    salida += "<h2>Competencias creadas</h2>"

    salida += "<table border='1' cellpadding='6'>"
    salida += """
    <tr>
        <th>Nombre</th>
        <th>Cupo</th>
        <th>Precio</th>
    </tr>
    """

    for d in distancias:

        salida += f"""
            <tr>
                <td>{d['nombre']}</td>
                <td>{d['cupo']}</td>
                <td>{d['precio']}</td>
                <td>
                    <form method="POST" style="display:inline;">
                        <input type="hidden" name="accion" value="eliminar">
                        <input type="hidden" name="distancia_id" value="{d['id']}">
                        <button onclick="return confirm('¿Eliminar distancia?')">
                            ❌
                        </button>
                    </form>
                </td>
            </tr>
            """
        

    salida += "</table>"
    return layout(salida, evento_id=evento_id)

    

@organizador_bp.route("/inscripcion/<numero>", methods=["GET","POST"])
def editar_inscripcion(numero):
    print(len(numero))
    print("NUMERO:", numero)
    print("DEBUG:", repr(numero))
    salida = ""
    tab = request.args.get("tab", "resumen")
    
    mensaje = ""
    if request.args.get("ok"):
        mensaje = """
        <div style="
            background:#d4edda;
            color:#155724;
            padding:10px;
            border-radius:5px;
            margin-bottom:15px;
        ">
            ✔ Cambios guardados correctamente
        </div>
        """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # -------------------------
    # GUARDAR CAMBIOS
    # -------------------------
    if request.method == "POST":

        accion = request.form.get("accion")

        if accion == "marcar_pagado":
            cursor.execute("""
            UPDATE inscripciones
            SET estado_pago = 'pagado'
            WHERE numero_inscripcion = %s
            """, (numero,))

            conn.commit()

            cursor.close()
            conn.close()

            return redirect(f"/inscripcion/{numero}?ok=1")

        # -------------------------
        # REGISTRAR PAGO MANUAL
        # -------------------------
             

        nombre = request.form["nombre"]
        apellido = request.form["apellido"]
        dni = request.form["dni"]
        email = request.form["email"]
        celular = request.form.get("celular")
        ciudad = request.form.get("ciudad")
        fecha_nac = request.form.get("fecha_nac") or None
        instagram = request.form.get("instagram")
        facebook = request.form.get("facebook")
        strava = request.form.get("strava")
        genero = request.form.get("genero")
        talle = request.form.get("talle_remera")
        team_id = request.form.get("team_id")

        if not team_id or team_id == "None":
            team_id = None
        else:
            team_id = int(team_id)
        team_nombre = request.form.get("team_input","").strip().upper()
        
        team_nombre = " ".join(team_nombre.split())
        dorsal = request.form.get("dorsal") or None
        distancia_id = request.form.get("distancia_id")

        if not distancia_id:
            distancia_id = ins["distancia_id"]
        
        team_id = request.form.get("team_id")
        team_nombre = request.form.get("team_input","").strip().upper()

        # normalizar
        if team_id in ["", "None", None]:
            team_id = None
        else:
            team_id = int(team_id)

        team_nombre = " ".join(team_nombre.split())

        # si no hay ID pero hay nombre → buscar o crear
        if not team_id and team_nombre:

            cursor.execute(
                "SELECT id FROM teams WHERE nombre=%s",
                (team_nombre,)
            )
            t = cursor.fetchone()

            if t:
                team_id = t["id"]
            else:
                cursor.execute(
                    "INSERT INTO teams (nombre,organizador_id) VALUES (%s,%s)",
                    (team_nombre,1)
                )
                conn.commit()
                team_id = cursor.lastrowid

        print("TEAM ID FINAL:", team_id)
        print("NUMERO:", numero)
        cursor.execute("""
        UPDATE personas
        SET nombre=%s,
            apellido=%s,
            dni=%s,
            email=%s,
            celular=%s,
            ciudad=%s,
            instagram=%s,
            facebook=%s,
            strava=%s,
            fecha_nac=%s,
            genero=%s,
            team_id=%s
        WHERE id = (
            SELECT persona_id
            FROM inscripciones
            WHERE numero_inscripcion=%s
        )
        """,(
            nombre,apellido,dni,email,celular,ciudad,
            instagram,facebook,strava,fecha_nac,
            genero,team_id,numero
        ))
        print("DISTANCIA RECIBIDA:", distancia_id)
        cursor.execute("""
        UPDATE inscripciones
        SET dorsal=%s,
            distancia_id=%s,
            talle_remera=%s
        WHERE numero_inscripcion=%s
        """, (dorsal, distancia_id, talle, numero))

        
        cursor.close()
        conn.close()

        tab = request.args.get("tab") or request.form.get("tab") or "resumen"
        return redirect(f"/inscripcion/{numero}?ok=1&tab={tab}")
    
    # -------------------------
    # CARGAR DATOS INSCRIPCION
    # -------------------------
    cursor.execute("""
    SELECT
        i.id,
        i.numero_inscripcion,
        i.fecha_inscripcion,
        i.estado_pago,
        i.dorsal,
        i.distancia_id,
        i.talle_remera,
        i.evento_id,           

        p.nombre,
        p.apellido,
        p.dni,
        p.email,
        p.celular,
        p.ciudad,
        p.fecha_nac,
        p.instagram,
        p.facebook,
        p.strava,
        p.genero,
        p.team_id,

        t.nombre AS team,
        d.nombre AS distancia

    FROM inscripciones i
    JOIN personas p ON p.id = i.persona_id
    JOIN distancias d ON d.id = i.distancia_id
    LEFT JOIN teams t ON p.team_id = t.id
    WHERE i.numero_inscripcion=%s
    """, (numero,))
    ins = cursor.fetchone()
    evento_id = ins["evento_id"]

    
    inscripcion_id = ins["id"]
    print("ID INSCRIPCION:", inscripcion_id)

    if ins and ins.get("fecha_nac"):
        ins["fecha_nac"] = ins["fecha_nac"].strftime("%Y-%m-%d")
    
    cursor.execute("""
    SELECT d.id, d.nombre
    FROM distancias d
    JOIN inscripciones i ON i.distancia_id = d.id
    WHERE i.numero_inscripcion = %s
    AND d.activo = 1
    ORDER BY d.nombre
    """, (numero,))

    distancias = cursor.fetchall()
    
    # =========================
    # PAGOS DE LA INSCRIPCION
    # =========================
    cursor.execute("""
    SELECT
        id,
        monto,
        metodo,
        estado,
        referencia_externa,
        fecha_creacion,
        fecha_confirmacion
    FROM pagos
    WHERE inscripcion_id = %s
    ORDER BY fecha_creacion DESC
    """, (inscripcion_id,))

    pagos = cursor.fetchall()

    # -------------------------
    # CARGAR TEAMS
    # -------------------------

    cursor.execute("SELECT id,nombre FROM teams ORDER BY nombre")
    teams = cursor.fetchall()

    if not ins:
        cursor.close()
        conn.close()
        return layout("<h2>Inscripción no encontrada</h2>")

    cursor.close()
    conn.close()

    # -------------------------
    # CONSTRUIR LISTA TEAMS
    # -------------------------
    lista_teams = ""

    for t in teams:
        lista_teams += f'<option value="{t["nombre"]}" data-id="{t["id"]}">'

    # -------------------------
    # HTML
    # -------------------------
    
    salida += f"""
    <script>

    function mostrar(seccion){{
        let resumen = document.getElementById("resumen")
        let corredor = document.getElementById("corredor")
        let pago = document.getElementById("pago")

        let secciones = {{
            resumen: resumen,
            corredor: corredor,
            pago: pago
        }}

        for (let key in secciones){{
            if(secciones[key]){{
                secciones[key].style.display = "none"
            }}
        }}

        if(secciones[seccion]){{
            secciones[seccion].style.display = "block"
        }}

        let input = document.getElementById("tab_actual")
        if(input){{
            input.value = seccion
        }}
    }}

    window.addEventListener("load", function(){{
        mostrar("{tab}")
    }})

    </script>
    """
    
    salida += mensaje

    salida += f"""
    <div style="margin-bottom:20px">

    <button type="button" onclick="mostrar('resumen')">Resumen</button>

    <button type="button" onclick="mostrar('corredor')">
    Datos del corredor
    </button>

    <button type="button" onclick="mostrar('pago')">
    Pagos
    </button>

    </div>
    """
    
    salida += f"""
    <form method="GET">

    <input type="hidden" name="tab" id="tab_actual" value="{tab}">

    <div id="resumen" style="display:none">

    <a href="/evento/{evento_id}/inscriptos" style="
    display:inline-block;
    margin-bottom:15px;
    padding:8px 15px;
    background:#4caf50;
    color:white;
    border-radius:6px;
    text-decoration:none;
    ">
    ← Volver a inscriptos
    </a>

    <h2>Resumen</h2>

    Código: {ins['numero_inscripcion']}<br><br>

    Distancia<br>
    <select name="distancia_id" style="width:220px;padding:6px;font-size:14px">
    """

    for d in distancias:

        selected = ""

        if d["id"] == ins["distancia_id"]:
            selected = "selected"

        salida += f"""
        <option value="{d['id']}" {selected}>
        {d['nombre']}
        </option>
        """

    # 🔥 TODO ESTO JUNTO
    salida += f"""
    </select><br><br>

    Fecha inscripción: {ins['fecha_inscripcion']}<br>
    Estado pago: {ins['estado_pago']}<br>
    Team: {ins.get('team','-')}<br>

    </div>

    <hr>
    """

    # ------------------- CORREDOR -------------------
    salida += f"""
    <div id="corredor" style="display:none">

    <h2>Datos del corredor</h2>

    Nombre<br>
    <input type="text" name="nombre" value="{ins['nombre']}"><br><br>

    Apellido<br>
    <input type="text" name="apellido" value="{ins['apellido']}"><br><br>

    DNI<br>
    <input type="text" name="dni" value="{ins['dni']}"><br><br>

    Email<br>
    <input type="email" name="email" value="{ins['email']}"><br><br>

    Celular<br>
    <input type="text" name="celular" value="{ins.get('celular','')}"><br><br>

    Ciudad<br>
    <input type="text" name="ciudad" value="{ins.get('ciudad','')}"><br><br>

    Fecha nacimiento<br>
    <input type="date" name="fecha_nac" value="{ins.get('fecha_nac','')}"><br><br>

    Edad<br>
    <input type="text" id="edad" readonly style="background:#eee"><br><br>

    Instagram<br>
    <input type="text" name="instagram" value="{ins.get('instagram','')}"><br><br>

    Facebook<br>
    <input type="text" name="facebook" value="{ins.get('facebook','')}"><br><br>

    Strava<br>
    <input type="text" name="strava" value="{ins.get('strava','')}"><br><br>

    Talle Remera<br>
    <select name="talle_remera">
        <option value="">Seleccionar</option>
        <option value="S" {"selected" if ins.get("talle_remera")=="S" else ""}>S</option>
        <option value="M" {"selected" if ins.get("talle_remera")=="M" else ""}>M</option>
        <option value="L" {"selected" if ins.get("talle_remera")=="L" else ""}>L</option>
        <option value="XL" {"selected" if ins.get("talle_remera")=="XL" else ""}>XL</option>
    </select><br><br>

    Team / Equipo<br>

    <input type="text" name="team_input" id="team_input"
    placeholder="Escribir equipo..."
    value="{'' if not ins.get('team') or ins.get('team').strip().lower() in ['none',''] else ins.get('team')}">

    <input type="hidden" name="team_id" id="team_id"
    value="{ins.get('team_id') if ins.get('team_id') else ''}">

    <div id="lista_teams" style="border:1px solid #ccc;max-height:120px;overflow:auto"></div>

    </div>
    """
    

    # ------------------- PAGOS -------------------
    salida += f"""
    <hr>

    <div id="pago" style="display:none">

    <h2>Pagos</h2>

    <form method="POST">
        <input type="hidden" name="accion" value="marcar_pagado">
        <button style="padding:10px;background:#4caf50;color:white;border:none;border-radius:5px">
            💰 Marcar como pagado
        </button>
    </form>

    <a href="/inscripcion/{numero}/pago"
    style="
    display:inline-block;
    padding:8px 12px;
    background:#1976d2;
    color:white;
    border-radius:6px;
    text-decoration:none;
    font-size:14px;
    ">
    Registrar pago manual
    </a>

    <br><br>

    <table border="1" cellpadding="6" style="border-collapse:collapse;width:100%">

    <tr style="background:#eee">
    <th>ID</th>
    <th>Monto</th>
    <th>Método</th>
    <th>Estado</th>
    <th>Referencia</th>
    <th>Creado</th>
    <th>Confirmado</th>
    <th>Editar</th>
    </tr>
    """

    # 🔥 FILAS
    if not pagos:
        salida += "<tr><td colspan='8'>Sin pagos registrados</td></tr>"
    else:
        for p in pagos:

            estado_clase = ""
            estado_texto = p['estado']

            if p['estado'] in ["aprobado", "pagado"]:
                estado_texto = "Confirmado"
                estado_clase = "background:#4caf50;color:white;padding:3px 6px;border-radius:4px"
            elif p['estado'] == "pendiente":
                estado_texto = "Pendiente"
                estado_clase = "background:#ff9800;color:white;padding:3px 6px;border-radius:4px"

            f_creacion = p['fecha_creacion'].strftime("%d/%m/%Y %H:%M") if p['fecha_creacion'] else "-"
            f_confirma = p['fecha_confirmacion'].strftime("%d/%m/%Y %H:%M") if p['fecha_confirmacion'] else "-"

            if p["metodo"] == "mercadopago":
                boton = "<span style='color:#888'>🔒</span>"
            else:
                boton = f"""
                <a href="/pago/{p['id']}/editar">
                    <button type="button">Editar</button>
                </a>
                """
            
            salida += f"""
            <tr>
                <td>{p['id']}</td>
                <td>${p['monto']}</td>
                <td>{p['metodo'] or 'Manual'}</td>
                <td><span style="{estado_clase}">{estado_texto}</span></td>
                <td>{p['referencia_externa'] or '-'}</td>
                <td>{f_creacion}</td>
                <td>{f_confirma}</td>
                <td>{boton}</td>
            </tr>
            """    

    salida += """
    </table>
    </div>

    <br><br>

    <button type="submit">
    Guardar cambios
    </button>

    </form>
    """

    salida += """
    <script>

    function calcularEdad(){
        let fechaInput = document.querySelector("input[name='fecha_nac']")
        let edadInput = document.getElementById("edad")

        if(!fechaInput || !edadInput) return

        let fecha = fechaInput.value
        if(!fecha){
            edadInput.value = ""
            return
        }

        let hoy = new Date()
        let fn = new Date(fecha)

        let edad = hoy.getFullYear() - fn.getFullYear()

        let m = hoy.getMonth() - fn.getMonth()

        if(m < 0 || (m === 0 && hoy.getDate() < fn.getDate())){
            edad--
        }

        edadInput.value = edad
    }

    // CLAVE: esperar un poquito
    setTimeout(calcularEdad, 200)

    // también al cambiar
    document.addEventListener("input", function(e){
        if(e.target.name === "fecha_nac"){
            calcularEdad()
        }
    })

    </script>
    """
    
    print("TAB ARGS:", request.args.get("tab"))
    print("TAB FINAL:", tab)
    
    salida += "<script>const teams = ["

    for t in teams:
        salida += f'{{ id: {t["id"]}, nombre: "{t["nombre"]}" }},'

    salida += "];</script>"

    

    salida += """
    <script>

    const input = document.getElementById("team_input");
    const hidden = document.getElementById("team_id");
    const lista = document.getElementById("lista_teams");

    if(input){
        input.addEventListener("keyup", function(){
            let texto = input.value.toLowerCase().trim();
            lista.innerHTML = "";
            hidden.value = "";

            if(texto.length === 0) return;

            let filtrados = teams.filter(t => 
                t.nombre.toLowerCase().includes(texto)
            );

            filtrados.forEach(t => {
                let div = document.createElement("div");
                div.innerText = t.nombre;

                div.onclick = function(){
                    input.value = t.nombre;
                    hidden.value = t.id;
                    lista.innerHTML = "";
                };

                lista.appendChild(div);
            });

            if(filtrados.length === 0){
                let nuevo = document.createElement("div");
                nuevo.innerText = "+ Crear equipo: " + input.value;

                nuevo.onclick = function(){
                    hidden.value = "";
                    lista.innerHTML = "";
                };

                lista.appendChild(nuevo);
            }
        });
    }

    </script>
    """

    return layout(salida)

    
@organizador_bp.route("/test_pago")
def test_pago():
    print("🔥 ENTRE A TEST")
    return "FUNCIONA TEST"   

@organizador_bp.route("/inscripcion/<numero>/pago", methods=["GET","POST"])
def pantalla_pago(numero):
    print("METHOD:", request.method)
    print("ENTRE A PANTALLA PAGO")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT i.id, d.precio, d.nombre
    FROM inscripciones i
    JOIN distancias d ON d.id = i.distancia_id
    WHERE i.numero_inscripcion = %s
    """, (numero,))

    info = cursor.fetchone()
    print("INFO:", info)

    if not info:
        return layout("<h2>Inscripción no encontrada</h2>")
    
    inscripcion_id = info["id"]

    
    if request.method == "POST":

        monto = request.form["monto"]
        estado = request.form["estado"]
        metodo = request.form["metodo"]
        
        cursor.execute("""
        SELECT id FROM pagos
        WHERE inscripcion_id = (
            SELECT id FROM inscripciones WHERE numero_inscripcion=%s
        )
        AND estado IN ('pagado','aprobado')
        """, (numero,))

        existe_pago = cursor.fetchone()

        if existe_pago:
            return "<h2>⚠️ Esta inscripción ya tiene un pago Confirmado</h2>"
        if estado == "aprobado":
            estado = "pagado"
        cursor.execute("""
        INSERT INTO pagos (inscripcion_id, monto, metodo, estado, fecha_creacion)
        VALUES (%s,%s,%s,%s,NOW())
        """, (inscripcion_id, monto, metodo, estado))

        conn.commit()

        cursor.execute("""
        UPDATE inscripciones
        SET estado_pago='pagado'
        WHERE id=%s
        """, (inscripcion_id))

        conn.commit()

        from flask import redirect
        return redirect(f"/inscripcion/{numero}?ok=1&tab=pago")
    
    
    return layout(f"""
    <h2>Registrar pago</h2>

    Distancia: {info['nombre']}<br><br>

    <form method="POST">

    Monto<br>
    <input type="number" name="monto" value="{float(info['precio'])}"><br><br>

    Estado<br>
    <select name="estado">
        <option value="pendiente">Pendiente</option>
        <option value="pagado">Pagado</option>
    </select><br><br>

    Metodo<br>
    <select name="metodo">
        <option value="manual">Manual</option>
        <option value="efectivo">Efectivo</option>
        <option value="transferencia">Transferencia</option>
    </select><br><br>

    <button type="submit">Guardar</button>

    </form>
    """)
    
# =========================
# EDITAR PAGO
# =========================
@organizador_bp.route("/pago/<int:pago_id>/editar", methods=["GET","POST"])
def editar_pago(pago_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # traer pago
    cursor.execute("""
    SELECT p.*, i.numero_inscripcion
    FROM pagos p
    JOIN inscripciones i ON i.id = p.inscripcion_id
    WHERE p.id = %s
    """, (pago_id,))

    pago = cursor.fetchone()

    if not pago:
        return layout("<h2>Pago no encontrado</h2>")

    if request.method == "POST":

        monto = request.form["monto"]
        estado = request.form["estado"]
        metodo = request.form["metodo"]

        if estado == "aprobado":
            estado = "pagado"

        cursor.execute("""
        UPDATE pagos
        SET monto=%s, metodo=%s, estado=%s
        WHERE id=%s
        """, (monto, metodo, estado, pago_id))

        cursor.execute("""
        UPDATE inscripciones
        SET estado_pago=%s
        WHERE id=%s
        """, (estado, pago["inscripcion_id"]))

        conn.commit()

        return redirect(f"/inscripcion/{pago['numero_inscripcion']}?ok=1&tab=pago")

    return layout(f"""
    <h2>Editar pago #{pago['id']}</h2>

    <form method="POST">

    Monto<br>
    <input type="number" name="monto" value="{pago['monto']}"><br><br>

    Estado<br>
    <select name="estado">
        <option value="pendiente" {"selected" if pago['estado']=="pendiente" else ""}>Pendiente</option>
        <option value="pagado" {"selected" if pago['estado'] in ['pagado','aprobado'] else ""}>Pagado</option>
    </select><br><br>

    Método<br>
    <select name="metodo">
        <option value="manual" {"selected" if pago['metodo']=="manual" else ""}>Manual</option>
        <option value="efectivo" {"selected" if pago['metodo']=="efectivo" else ""}>Efectivo</option>
        <option value="transferencia" {"selected" if pago['metodo']=="transferencia" else ""}>Transferencia</option>
    </select><br><br>

    <button type="submit">Guardar cambios</button>

    </form>
    """)
# -------------------------
# EDITAR EVENTO
# -------------------------

@organizador_bp.route("/evento/<int:evento_id>/editar", methods=["GET","POST"])
def editar_evento(evento_id):
    print(request.form)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # =========================
    # POST (GUARDAR)
    # =========================
    if request.method == "POST":

        # 🔹 traer evento actual para conservar archivos existentes
        cursor.execute("SELECT * FROM eventos WHERE id=%s", (evento_id,))
        evento = cursor.fetchone()

        nombre = request.form["nombre"]
        fecha = request.form["fecha"]
        hora = request.form["hora"]
        lugar = request.form["lugar"]
        provincia = request.form["provincia"]
        descripcion = request.form.get("descripcion", "")

        archivo_reglamento = request.files.get("reglamento_pdf")
        archivo_deslinde = request.files.get("deslinde_pdf")

        direccion = request.form.get("direccion")
        latitud = request.form.get("latitud")
        longitud = request.form.get("longitud")

        latitud = float(latitud) if latitud not in [None, "", "None"] else None
        longitud = float(longitud) if longitud not in [None, "", "None"] else None

        archivo = request.files.get("imagen")
        imagen = evento.get("imagen")

        # conservar valores actuales
        reglamento = evento.get("reglamento_archivo")
        deslinde = evento.get("deslinde_archivo")

        reglamento_activo = evento.get("reglamento_activo", 0)
        deslinde_activo = evento.get("deslinde_activo", 0)

        # -------------------------
        # DOCUMENTOS
        # -------------------------
        carpeta_docs = "static/documentos"
        if not os.path.exists(carpeta_docs):
            os.makedirs(carpeta_docs)

        if archivo_reglamento and archivo_reglamento.filename != "":
            nombre_reglamento = secure_filename(archivo_reglamento.filename)
            ruta = os.path.join(carpeta_docs, nombre_reglamento)
            archivo_reglamento.save(ruta)

            reglamento = nombre_reglamento
            reglamento_activo = 1

        if archivo_deslinde and archivo_deslinde.filename != "":
            nombre_deslinde = secure_filename(archivo_deslinde.filename)
            ruta = os.path.join(carpeta_docs, nombre_deslinde)
            archivo_deslinde.save(ruta)

            deslinde = nombre_deslinde
            deslinde_activo = 1

        # -------------------------
        # IMAGEN
        # -------------------------
        if archivo and archivo.filename != "":
            nombre_archivo = secure_filename(archivo.filename)

            carpeta = "static/eventos"
            if not os.path.exists(carpeta):
                os.makedirs(carpeta)

            ruta = os.path.join(carpeta, nombre_archivo)
            archivo.save(ruta)

            imagen = nombre_archivo

        # -------------------------
        # UPDATE
        # -------------------------
        cursor.execute("""
        UPDATE eventos
        SET nombre=%s,
            fecha=%s,
            hora=%s,
            lugar=%s,
            provincia=%s,
            descripcion=%s,
            direccion=%s,
            latitud=%s,
            longitud=%s,
            imagen=%s,
            reglamento_archivo=%s,
            reglamento_activo=%s,
            deslinde_archivo=%s,
            deslinde_activo=%s
        WHERE id=%s
        """, (
            nombre,
            fecha,
            hora,
            lugar,
            provincia,
            descripcion,
            direccion,
            latitud,
            longitud,
            imagen,
            reglamento,
            reglamento_activo,
            deslinde,
            deslinde_activo,
            evento_id
        ))

        conn.commit()
        cursor.close()
        conn.close()
        return f"""
        <script>
        alert("Evento actualizado");
        window.location.href="/evento/{evento_id}/panel";
        </script>
        """

    # =========================
    # GET
    # =========================
    cursor.execute("SELECT * FROM eventos WHERE id=%s",(evento_id,))
    evento = cursor.fetchone()

    hora = evento.get("hora")

    if hora:
        try:
            hora = hora.strftime("%H:%M")
        except:
            hora = str(hora)[:5]
    else:
        hora = ""

    cursor.close()
    conn.close()

    salida = f"""
    <form method="POST" enctype="multipart/form-data">

    <h2>Editar evento</h2>

    Nombre del evento<br>
    <input type="text" name="nombre" value="{evento.get('nombre','')}" style="width:400px"><br><br>

    Fecha<br>
    <input type="date" name="fecha" value="{evento.get('fecha','')}"><br><br>

    Hora<br>
    <input type="time" name="hora" value="{str(hora)[:5] if hora else ''}"><br><br>

    Lugar<br>
    <input type="text" name="lugar" value="{evento.get('lugar','')}" style="width:400px"><br><br>

    Provincia<br>
    <input type="text" name="provincia" value="{evento.get('provincia','')}" style="width:400px"><br><br>

    <h3>Descripción</h3>
    <button type="button" onclick="document.getElementById('subirImgEditor').click()" style="
    padding:10px 16px;
    background:#1565c0;
    color:white;
    border:none;
    border-radius:6px;
    cursor:pointer;
    margin-bottom:10px;
    ">
    📷 Insertar imagen
    </button>

<input type="file" id="subirImgEditor" accept="image/*" style="display:none">
    <textarea id="editor" name="descripcion" style="width:100%;height:200px;">
    {evento.get("descripcion","")}
    </textarea><br><br>

    <h3>Ubicación del evento</h3>

    <input type="text" id="direccion" name="direccion"
    value="{evento.get('direccion','')}"
    style="width:400px"><br><br>

    <input type="hidden" id="latitud" name="latitud"
    value="{evento.get('latitud','')}">

    <input type="hidden" id="longitud" name="longitud"
    value="{evento.get('longitud','')}">

    <div style="max-width:400px;margin-top:10px">
        <div id="map" style="width:100%;height:180px;border-radius:10px"></div>
    </div>

    <br><br>

    <h3>Imagen</h3>

    <input type="file" name="imagen" accept="image/*" onchange="previewImagen(event)"><br><br>

    <img id="preview" style="max-width:200px;border-radius:8px;display:none">

    <img src="/static/eventos/{evento.get('imagen') or 'logo.png'}"
    style="max-width:200px;border-radius:8px;"><br><br>

    <h3>Reglamento (PDF)</h3>
    <input type="file" name="reglamento_pdf" accept=".pdf"><br>
    Archivo actual: {evento.get('reglamento','Sin archivo')}<br><br>

    <h3>Deslinde (PDF)</h3>
    <input type="file" name="deslinde_pdf" accept=".pdf"><br>
    Archivo actual: {evento.get('deslinde','Sin archivo')}<br><br>

    <button type="submit" style="
    padding:10px 20px;
    background:#222;
    color:white;
    border:none;
    border-radius:6px;
    cursor:pointer;
    ">
    Guardar cambios
    </button>
    
    <script>
    document.querySelector("form").addEventListener("submit", function() {{
        for (var instance in CKEDITOR.instances) {{
            CKEDITOR.instances[instance].updateElement();
        }}
    }});
    </script>

    </form>
    """
    salida += """
    <script>
    function previewImagen(event){
        const input = event.target;
        const preview = document.getElementById("preview");

        if(input.files && input.files[0]){
            const reader = new FileReader();

            reader.onload = function(e){
                preview.src = e.target.result;
                preview.style.display = "block";
            }

            reader.readAsDataURL(input.files[0]);
        }
    }
    document.getElementById("subirImgEditor").addEventListener("change", async function () {

        const archivo = this.files[0];
        if (!archivo) return;

        const datos = new FormData();
        datos.append("upload", archivo);

        const resp = await fetch("/subir_imagen_simple", {
            method: "POST",
            body: datos
        });

        const json = await resp.json();

        if (json.url) {
            CKEDITOR.instances.editor.insertHtml(
                '<p><img src="' + json.url + '" style="max-width:100%;"></p>'
            );
        } else {
            alert("Error al subir imagen");
        }

        this.value = "";
    });
    </script>
    """
    # =========================
    # CKEDITOR
    # =========================
    salida += """
        <script src="https://cdn.ckeditor.com/4.22.1/full/ckeditor.js"></script>

        <script>
        CKEDITOR.replace('editor', {
        height: 350,
        uploadUrl: '/subir_imagen',
        filebrowserUploadUrl: '/subir_imagen',
        filebrowserUploadMethod: 'form',

        toolbar: [
            { name: 'styles', items: ['Format','Font','FontSize'] },
            { name: 'basicstyles', items: ['Bold','Italic','Underline','Strike'] },
            { name: 'colors', items: ['TextColor','BGColor'] },
            { name: 'paragraph', items: ['NumberedList','BulletedList','Outdent','Indent','Blockquote'] },
            { name: 'links', items: ['Link','Unlink'] },
            { name: 'insert', items: ['UploadImage','Image','Table','HorizontalRule'] },
            { name: 'clipboard', items: ['Undo','Redo'] },
            { name: 'tools', items: ['Maximize','Source'] }
        ],

        removeButtons: '',
        allowedContent: true
    });
    </script>
    """

    
        

    # =========================
    # MAPA
    # =========================
    salida += f"""
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAO2tAZ13XqjSbEPBk7CUqybYU3PBajFGk&libraries=places&callback=initMap" async defer></script>

    <script>
    function initMap() {{

        let lat = {evento.get("latitud") or -34.8};
        let lng = {evento.get("longitud") or -58.3};

        const map = new google.maps.Map(document.getElementById("map"), {{
            center: {{ lat: lat, lng: lng }},
            zoom: 15
        }});

        const marker = new google.maps.Marker({{
            position: {{ lat: lat, lng: lng }},
            map: map,
            draggable: true
        }});

        marker.addListener("dragend", function () {{
            document.getElementById("latitud").value = marker.getPosition().lat();
            document.getElementById("longitud").value = marker.getPosition().lng();
        }});

        const input = document.getElementById("direccion");
        const autocomplete = new google.maps.places.Autocomplete(input);

        autocomplete.addListener("place_changed", function () {{
            const place = autocomplete.getPlace();

            if (!place.geometry) return;

            map.setCenter(place.geometry.location);
            marker.setPosition(place.geometry.location);

            document.getElementById("latitud").value = place.geometry.location.lat();
            document.getElementById("longitud").value = place.geometry.location.lng();
        }});
    }}

    
    </script>
    """

    return layout(salida)

# ---------------------------------------------------
# SUBIR IMÁGENES DESDE EL EDITOR
# ---------------------------------------------------

@organizador_bp.route("/subir_imagen", methods=["POST"])
def subir_imagen():

    archivo = request.files.get("upload")

    if not archivo:
        return jsonify({
            "uploaded": False,
            "error": {
                "message": "No se pudo subir el archivo"
            }
        })

    import time

    import time
    import uuid

    extension = archivo.filename.rsplit(".", 1)[-1].lower()
    nombre = f"{int(time.time())}_{uuid.uuid4().hex[:6]}.{extension}"

    carpeta = os.path.join("static", "mapas")

    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    ruta = os.path.join(carpeta, nombre)

    img = Image.open(archivo)
    img.thumbnail((1200,800))
    img.save(ruta)

    url = f"/static/mapas/{nombre}"

    # ESTE JSON ES EL QUE CKEDITOR ESPERA
    func_num = request.args.get("CKEditorFuncNum")

    return f"""
    <script>
    window.parent.CKEDITOR.tools.callFunction(
        {func_num},
        "{url}",
        "Imagen subida correctamente"
    );
    </script>
    """
@organizador_bp.route("/evento/<int:evento_id>/publicar")
def publicar_evento(evento_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE eventos SET publicado = 1 WHERE id = %s", (evento_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/evento/{evento_id}/panel")

@organizador_bp.route("/evento/<int:evento_id>/ocultar")
def ocultar_evento(evento_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE eventos SET publicado = 0 WHERE id = %s", (evento_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/evento/{evento_id}/panel")

@organizador_bp.route("/evento/<int:evento_id>/exportar")
def pantalla_exportar(evento_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, nombre
        FROM distancias
        WHERE evento_id = %s
    """, (evento_id,))

    distancias = cursor.fetchall()

    cursor.close()
    conn.close()

    salida = f"""
    <h2>Exportar participantes</h2>

    <form method="GET" action="/evento/{evento_id}/exportar_excel">

    Estado:<br>
    <select name="estado">
        <option value="">Todos</option>
        <option value="pagado">Pagados</option>
        <option value="pendiente">Pendientes</option>
    </select><br><br>

    Distancia:<br>
    <select name="distancia">
        <option value="">Todas</option>
    """

    for d in distancias:
        salida += f"<option value='{d['id']}'>{d['nombre']}</option>"

    salida += """
    </select><br><br>

    <button type="submit">
        Generar Excel
    </button>

    </form>
    """

    return layout(salida)
@organizador_bp.route("/subir_imagen_simple", methods=["POST"])
def subir_imagen_simple():

    archivo = request.files.get("upload")

    if not archivo:
        return jsonify({"error": "sin archivo"})

    import time, uuid

    extension = archivo.filename.rsplit(".", 1)[-1].lower()
    nombre = f"{int(time.time())}_{uuid.uuid4().hex[:6]}.{extension}"

    carpeta = os.path.join("static", "mapas")
    os.makedirs(carpeta, exist_ok=True)

    ruta = os.path.join(carpeta, nombre)

    img = Image.open(archivo)
    img.thumbnail((1200,800))
    img.save(ruta)

    url = f"/static/mapas/{nombre}"

    return jsonify({
        "url": url
    })
@organizador_bp.route("/evento/<int:evento_id>/exportar_excel")
def exportar_excel(evento_id):

    estado = request.args.get("estado")
    distancia = request.args.get("distancia")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nombre FROM eventos WHERE id = %s", (evento_id,))
    evento = cursor.fetchone()
    nombre_evento = evento["nombre"]
    query = """
    SELECT
        e.nombre AS evento,
        i.numero_inscripcion,
        p.nombre,
        p.apellido,
        p.dni,
        p.email,
        p.fecha_nac,
        p.genero,
        c.nombre AS categoria,
        p.ciudad,
        p.direccion,
        pa.nombre AS pais,
        prov.nombre AS provincia,
        d.nombre AS distancia,        
        i.estado_pago,
        pay.monto_total AS monto_pagado,
        pay.fecha_pago,
        i.fecha_inscripcion,        
        i.dorsal,
        i.talle_remera,
        t.nombre AS team
    FROM inscripciones i
    JOIN personas p ON p.id = i.persona_id
    JOIN distancias d ON d.id = i.distancia_id
    LEFT JOIN teams t ON t.id = p.team_id
    LEFT JOIN provincias prov ON prov.id = p.provincia_id
    LEFT JOIN paises pa ON pa.id = p.pais_id
    LEFT JOIN categorias c ON c.id = i.categoria_id
    LEFT JOIN (
        SELECT 
            inscripcion_id,
            SUM(monto) AS monto_total,
            MAX(fecha_confirmacion) AS fecha_pago
        FROM pagos
        WHERE estado IN ('pagado','aprobado')
        GROUP BY inscripcion_id
    ) pay ON pay.inscripcion_id = i.id
    JOIN eventos e ON e.id = i.evento_id
    WHERE i.evento_id = %s
    """

    params = [evento_id]

    # filtro estado
    if estado:
        if estado == "pagado":
            query += " AND i.estado_pago = 'pagado'"
        else:
            query += " AND i.estado_pago = %s"
            params.append(estado)

    # filtro distancia
    if distancia:
        query += " AND i.distancia_id = %s"
        params.append(distancia)

    cursor.execute(query, params)
    datos = cursor.fetchall()
    cursor.close()
    conn.close()

    # 🧾 CREAR EXCEL
    wb = Workbook()
    ws = wb.active
    ws.title = "Participantes"

    # encabezados
    ws.append([
        "Evento",
        "Código",
        "Nombre",
        "Apellido",
        "DNI",
        "Email",
        "Fecha Nacimiento",
        "Edad",
        "Género",
        "Categoría",
        "Provincia",
        "País",        
        "Ciudad",
        "Dirección",
        "Distancia",
        "Estado",
        "Monto Pagado",
        "Fecha Pago",
        "Fecha inscripción",        
        "Dorsal",
        "Team",
        "Talle Remera"
    ])
    from datetime import date

    for d in datos:

        # calcular edad
        edad = ""
        if d["fecha_nac"]:
            hoy = date.today()
            fn = d["fecha_nac"]
            edad = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

        # estado
        estado_txt = "Pagado" if d["estado_pago"] in ["pagado","aprobado"] else "Pendiente"

        ws.append([
            d["evento"],
            d["numero_inscripcion"],
            d["nombre"],
            d["apellido"],
            int(d["dni"]) if d["dni"] else "",
            d["email"],
            d["fecha_nac"].strftime("%d/%m/%Y") if d["fecha_nac"] else "",
            edad,
            d["genero"] or "",
            d["categoria"] or "",
            d["provincia"] or "",
            d["pais"] or "",
            d["ciudad"] or "",
            d["direccion"] or "",
            d["distancia"],
            estado_txt,
            d["monto_pagado"] or "",  # 💰 NUEVO
            d["fecha_pago"].strftime("%d/%m/%Y %H:%M") if d["fecha_pago"] else "",
            d["fecha_inscripcion"].strftime("%d/%m/%Y %H:%M") if d["fecha_inscripcion"] else "",
            d["dorsal"] or "",
            d["team"] or "",
            d["talle_remera"] or ""
        ])
    # guardar en memoria
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    import re
    nombre_limpio = re.sub(r'[^a-zA-Z0-9]+', '_', nombre_evento).lower()

    return send_file(
        output,
        download_name=f"participantes_{nombre_limpio}.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
@organizador_bp.route("/evento/<int:evento_id>/exportar_seguro")
def exportar_seguro(evento_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # nombre evento
    cursor.execute("SELECT nombre FROM eventos WHERE id = %s", (evento_id,))
    evento = cursor.fetchone()
    nombre_evento = evento["nombre"]

    # datos simples para seguro
    cursor.execute("""
    SELECT
        e.nombre AS evento,
        p.apellido,
        p.nombre,
        p.dni,
        p.fecha_nac,
        p.genero,
        p.ciudad,
        d.nombre AS distancia
    FROM inscripciones i
    JOIN personas p ON p.id = i.persona_id
    JOIN distancias d ON d.id = i.distancia_id
    JOIN eventos e ON e.id = i.evento_id
    WHERE i.evento_id = %s
    """, (evento_id,))

    datos = cursor.fetchall()
    cursor.close()
    conn.close()

    # crear excel
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Seguro"

    # encabezados
    ws.append([
        "Evento",
        "Apellido",
        "Nombre",
        "DNI",
        "Fecha Nacimiento",
        "Edad",
        "Género",
        "Ciudad",
        "Distancia"
    ])

    from datetime import date

    for d in datos:

        # calcular edad
        edad = ""
        if d["fecha_nac"]:
            hoy = date.today()
            fn = d["fecha_nac"]
            edad = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

        ws.append([
            d["evento"],
            d["apellido"],
            d["nombre"],
            int(d["dni"]) if d["dni"] else "",
            d["fecha_nac"].strftime("%d/%m/%Y") if d["fecha_nac"] else "",
            edad,
            d["genero"] or "",
            d["ciudad"] or "",
            d["distancia"]
        ])

    # guardar en memoria
    import io
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    # limpiar nombre evento
    import re
    nombre_limpio = re.sub(r'[^a-zA-Z0-9]+', '_', nombre_evento).lower()

    return send_file(
        output,
        download_name=f"seguro_{nombre_limpio}.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )