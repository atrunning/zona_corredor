import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = "mail.zonacorredor.com.ar"
SMTP_PORT = 587

SMTP_USER = "inscripciones@zonacorredor.com.ar"
SMTP_PASS = "TU_PASSWORD"


def enviar_mail(destino, asunto, html):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = destino
        msg["Subject"] = asunto

        msg.attach(MIMEText(html, "html"))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        print("Error mail:", e)
        return False


def prueba_mail():
    print("mail.py funcionando")


def enviar_confirmacion(destino, nombre, dni, carrera, fecha, distancia, numero, imagen):

    html = f"""
    <div style="font-family:Arial; max-width:700px; margin:auto; background:#ffffff; border:1px solid #ddd; border-radius:12px; overflow:hidden;">

        <img src="{imagen}" style="width:100%; max-height:320px; object-fit:cover;">

        <div style="padding:30px; text-align:center;">

            <h1 style="color:#2e7d32; margin-bottom:10px;">
                ✅ INSCRIPCIÓN CONFIRMADA
            </h1>

            <h2 style="margin:0; color:#222;">
                {carrera}
            </h2>

            <p style="font-size:18px; color:#555;">
                {fecha}
            </p>

            <hr style="margin:25px 0;">

            <p style="font-size:18px;"><b>Corredor:</b> {nombre}</p>
            <p style="font-size:18px;"><b>DNI:</b> {dni}</p>
            <p style="font-size:18px;"><b>Distancia:</b> {distancia}</p>

            <div style="
                margin:30px auto;
                width:220px;
                height:220px;
                border:2px dashed #999;
                display:flex;
                align-items:center;
                justify-content:center;
                color:#666;
                font-size:14px;
            ">
                QR {numero}
            </div>

            <p style="font-size:22px; font-weight:bold; color:#1976d2;">
                N° {numero}
            </p>

            <p style="margin-top:25px; color:#666;">
                Presentá este comprobante en la acreditación.
            </p>

            <p style="margin-top:30px; font-size:13px; color:#999;">
                Powered by Zona Corredor
            </p>

        </div>
    </div>
    """

    if SMTP_PASS == "TU_PASSWORD":
        print("MAIL A:", destino)
        print("Nombre:", nombre)
        print("DNI:", dni)
        print("Carrera:", carrera)
        return True

    return enviar_mail(
        destino,
        "Inscripción confirmada",
        html
    )