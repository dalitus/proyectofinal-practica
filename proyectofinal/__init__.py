"""Paquete de la aplicacion.

Sin imports: los efectos de registro de paginas viven en
``proyectofinal/proyectofinal.py``, que es el modulo que Reflex importa. Tener
imports aca obligaba a cargar paginas, estados y repositorios solo para leer un
modelo (y rompia Alembic, que solo necesita el paquete ``model``).
"""
