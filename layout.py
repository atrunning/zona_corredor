def layout(contenido, menu=True, evento_id=None, eventos=None):

    menu_html = ""

    if menu:
        menu_html = "<div style='width:200px;background:#f0f0f0;padding:20px;height:100vh'>"
        menu_html += "<h3>Menú</h3>"

        if evento_id:
            menu_html += f"""
            <a href="/organizador">📋 Eventos</a><br>
            <a href="/evento/{evento_id}/panel">Panel</a><br><br>
            <a href="/evento/{evento_id}/inscriptos">Inscriptos</a><br><br>
            <a href="/evento/{evento_id}/reporte_remeras">Remeras</a><br><br>
            """

        menu_html += "</div>"

    return f"""
    <html>
    <body style="font-family:Arial;margin:0">

    <div style="display:flex">

        {menu_html}

        <div style="padding:20px;width:100%">
            {contenido}
        </div>

    </div>

    </body>
    </html>
    """