import os

import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in the "
        "database credentials (D-011)."
    )

config = rx.Config(
    app_name="app",
    upload_dir="static",
    db_url=DATABASE_URL,
    disable_plugins=[SitemapPlugin],  # opcional: silencia warning
    plugins=[rx.plugins.RadixThemesPlugin()],  # explicito: evita el warning de 0.9
    # La UI es solo clara (docs/design.md). Sin esto, un sistema operativo en
    # modo oscuro pinta el texto casi blanco sobre nuestros fondos blancos.
    default_color_mode="light",
)
