import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin

import os
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

config = rx.Config(
    app_name="proyectofinal",
    upload_dir="static",
    db_url=os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3306/zapateria_db"
    ),
    disable_plugins=[SitemapPlugin],  # opcional: silencia warning
    plugins=[rx.plugins.RadixThemesPlugin()],  # explicito: evita el warning de 0.9
    # La UI es solo clara (docs/design.md). Sin esto, un sistema operativo en
    # modo oscuro pinta el texto casi blanco sobre nuestros fondos blancos.
    default_color_mode="light",
)