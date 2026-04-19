import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = "smtp-relay.brevo.com"
SMTP_PORT = 587

SMTP_USER = "a8939b001@smtp-brevo.com"
SMTP_PASS = "N5nK1L9mZDtAFGP2"


def prueba_mail():
    print("mail.py funcionando")


def enviar_mail(destino, asunto, html):
    try:
        print("INICIANDO SMTP")

        msg = MIMEMultipart("alternative")
        msg["From"] = SMTP_USER
        msg["To"] = destino
        msg["Subject"] = asunto

        msg.attach(MIMEText(html, "html", "utf-8"))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        print("CONECTO")

        server.ehlo()
        print("EHLO OK")

        server.starttls()
        print("TLS OK")

        server.ehlo()

        server.login(SMTP_USER, SMTP_PASS)
        print("LOGIN OK")

        server.send_message(msg)
        print("SEND OK")

        server.quit()
        print("QUIT OK")

        print("MAIL ENVIADO A:", destino)
        return True

    except Exception as e:
        print("Error mail:", e)
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