Sistema de Gestión de Productos

Aplicación web para la gestión de productos, usuarios y ventas, panel de administración, y carga automatizada de imágenes.


Descripción

Este sistema permite a administradores y usuarios gestionar productos, realizar operaciones CRUD, visualizar estadísticas y automatizar la carga de imágenes mediante integración con Google Drive. Diseñado para ser modular, escalable y fácil de mantener.

Estructura del Proyecto

📁 app/
├── 📁 pages/              # Páginas de usuario y admin
├── 📁 components/         # Componentes reutilizables
├── 📁 models/             # Modelos SQLModel
├── 📁 services/           # Lógica de negocio y carga de imágenes
├── 📁 utils/              # Validaciones, helpers, constantes
├── 📁 assets/             # Imágenes y archivos estáticos
├── main.py               # Punto de entrada

Tecnologías utilizadas

	Python
	Reflex
	SQLModel
	SQLAlchemy
	MySQL


Instalación y configuración

	Clonar el repositorio.
	Crear un entorno virtual.
	Instalar dependencias con pip install -r requirements.txt.
	Configurar variables de entorno para la base de datos.
	Ejecutar migraciones con Alembic, mekemigrate y migert.
	Modificar la función connect_db para que se conecte correctamente a la base de datos.
	Clonar el repositorio.
	Crear un entorno virtual.
	Instalar dependencias con pip install -r requirements.txt.
	Configurar variables de entorno para la base de datos.
	Ejecutar migraciones con Alembic.


Base de datos y migraciones

	Se utiliza MySQL como sistema gestor.
	Las migraciones se manejan con Alembic, mekemigrate y migert.
	El modelo de datos está definido con SQLModel.
	Se utiliza MySQL como sistema gestor.
	Las migraciones se manejan con Alembic y herramientas como mekemigrate y migert.
	El modelo de datos está definido con SQLModel.
	Se utiliza MySQL como sistema gestor.
	Las migraciones se manejan con Alembic y herramientas como mekemigrate y migert.
	El modelo de datos está definido con SQLModel.
	
	
Carga de imágenes

	Las imágenes se suben y gestionan mediante integración con Google Drive.
	Se validan URLs y se implementan imágenes por defecto en caso de error.
	