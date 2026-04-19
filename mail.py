import os
import requests

# =========================
# CONFIGURACION API BREVO
# =========================
BREVO_API_KEY = os.getenv("BREVO_API_KEY")


def prueba_mail():
    print("mail.py funcionando con API Brevo")


def enviar_mail(destino, asunto, html):
    try:
        print("===== INICIANDO API BREVO =====")

        if not BREVO_API_KEY:
            print("Falta variable BREVO_API_KEY")
            return False

        url = "https://api.brevo.com/v3/smtp/email"

        headers = {
            "accept": "application/json",
            "api-key": BREVO_API_KEY,
            "content-type": "application/json"
        }

        payload = {
            "sender": {
                "name": "Zona Corredor",
                "email": "zonacorredor@gmail.com"
            },
            "to": [
                {
                    "email": destino
                }
            ],
            "subject": asunto,
            "htmlContent": html
        }

        r = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=20
        )

        print("STATUS:", r.status_code)
        print("RESPUESTA:", r.text)

        return r.status_code in [200, 201, 202]

    except Exception as e:
        print("ERROR MAIL:", repr(e))
        return False


def enviar_confirmacion(
    destino,
    nombre,
    dni,
    carrera,
    fecha,
    distancia,
    numero,
    imagen
):

    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>

    <body style="margin:0; padding:8px; background:#f4f4f4;">

    <div style="
        font-family:Arial,sans-serif;
        max-width:280px;
        margin:auto;
        background:#ffffff;
        border:1px solid #ddd;
        border-radius:10px;
        overflow:hidden;
    ">

        <img src="{imagen}"
             style="width:100%; height:100px; object-fit:cover; display:block;">

        <div style="padding:10px; text-align:center;">

            <h1 style="
                margin:0;
                font-size:10px;
                color:#2e7d32;
                line-height:1.2;
            ">
                ✅ CONFIRMADA
            </h1>

            <h2 style="
                margin:6px 0 3px 0;
                font-size:13px;
                color:#222;
            ">
                {carrera}
            </h2>

            <p style="
                margin:0;
                font-size:11px;
                color:#666;
            ">
                {fecha}
            </p>

            <hr style="margin:10px 0;">

            <p style="margin:4px 0; font-size:12px;">
                <b>{nombre}</b>
            </p>

            <p style="margin:4px 0; font-size:11px;">
                DNI {dni}
            </p>

            <p style="margin:4px 0; font-size:11px;">
                {distancia}
            </p>

            <div style="
                margin:12px auto;
                padding:8px;
                border:1px solid #ddd;
                border-radius:8px;
                background:#f8f8f8;
            ">

                <div style="
                    font-size:10px;
                    color:#666;
                ">
                    Número
                </div>

                <div style="
                    font-size:18px;
                    font-weight:bold;
                    color:#1565c0;
                    margin-top:4px;
                ">
                    {numero}
                </div>

            </div>

            <p style="
                font-size:10px;
                color:#555;
                margin:6px 0;
            ">
                Presentar en acreditación
            </p>

        </div>
    </div>

    </body>
    </html>
    """

    return enviar_mail(
        destino,
        "Inscripción confirmada",
        html
    )