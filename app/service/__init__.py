"""Reglas de negocio y validacion.

Sin re-exports: cada consumidor importa el servicio que usa por nombre
(``from app.service.auth_servicio import ...``). El ``__init__``
vacio evita cargar todos los servicios al importar uno solo.
"""
