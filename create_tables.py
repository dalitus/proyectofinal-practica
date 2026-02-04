"""Script para crear la tabla pedidos"""
from sqlmodel import SQLModel
from proyectofinal.model.pedido_model import Pedido
from proyectofinal.repository.conect_db import engine

# Crear todas las tablas
SQLModel.metadata.create_all(engine)
print("Tabla 'pedidos' creada exitosamente!")
