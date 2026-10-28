"""Acceso a datos.

Sin re-exports: cada modulo importa su repositorio por nombre
(``from app.repository.producto_repocitory import ...``). El
``__init__`` vacio evita cargar todo el arbol de repositorios al importar uno
solo (y rompia los tests y Alembic cuando alguno quedaba a medio migrar).
"""
