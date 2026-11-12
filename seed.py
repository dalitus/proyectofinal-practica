"""Seed inicial: administrador y catalogo de ejemplo.

Uso:
    .\\.venv\\Scripts\\python.exe seed.py

Es idempotente: si el admin, una categoria o un producto ya existen, no los
duplica. El admin sale de ``ADMIN_EMAIL`` / ``ADMIN_PASSWORD`` en ``.env``
(D-013); no hay credenciales por defecto en el codigo.

Catalogo
--------
Los 30 productos salen del catalogo publico de Topper, Fila y Asics Argentina
(relevados el 2026-11-11): nombre, marca, precio de lista, colores, talles y
stock disponible son datos reales de esas tiendas. Las descripciones son
propias y las imagenes se enlazan desde el CDN publico de cada marca.

El proyecto es academico y no comercial (D-054): no se copian textos de
marketing ni se descargan las imagenes al repositorio. Para reemplazar una
imagen alcanza con subir una propia desde el panel de administracion.
"""

from __future__ import annotations

import os
from decimal import Decimal

from dotenv import load_dotenv
from sqlmodel import Session, select

from app.model.categoria_modelo import Categoria
from app.model.producto_modelo import Producto
from app.model.variante_modelo import Stocks
from app.repository.base_de_datos import get_session
from app.service.auth_servicio import ErrorDeRegistro, crear_admin_si_no_existe

load_dotenv()

ADMIN_NOMBRE = os.getenv("ADMIN_NOMBRE", "Administrador")

CATEGORIAS = ["Running", "Urbano", "Outdoor", "Infantil", "Verano", "Fútbol", "Tenis"]

PRODUCTOS = [
    {
        "nombre": "Zapatilla Topper Fast 2.0",
        "descripcion": "Zapatilla liviana de malla para el día a día, con suela de goma flexible.",
        "precio": Decimal("52900.00"),
        "marca": "Topper",
        "categoria": "Urbano",
        "imagen": "https://topperarg.vteximg.com.br/arquivos/ids/552106-600-600/26442_1.jpg?v=639288871907600000",
        "variantes": [
            (
                "Celeste/Lima/Beige",
                [
                    ("35", 6),
                    ("36", 7),
                    ("37", 8),
                    ("38", 1),
                    ("39", 1),
                    ("40", 1),
                    ("41", 4),
                    ("42", 5),
                ],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Topper Kick Run",
        "descripcion": (
            "Pensada para salidas cortas y entrenamiento urbano, con buena amortiguación."
        ),
        "precio": Decimal("76999.00"),
        "marca": "Topper",
        "categoria": "Running",
        "imagen": "https://topperarg.vteximg.com.br/arquivos/ids/533921-600-600/27497.jpg?v=639197325909570000",
        "variantes": [
            (
                "Gris/Negro/Beige",
                [
                    ("35", 1),
                    ("36", 2),
                    ("37", 0),
                    ("38", 0),
                    ("39", 5),
                    ("40", 3),
                    ("41", 4),
                    ("42", 5),
                ],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Topper Leroi",
        "descripcion": "Estilo retro en cuero sintético, ideal para combinar con joggers y jeans.",
        "precio": Decimal("63999.00"),
        "marca": "Topper",
        "categoria": "Urbano",
        "imagen": "https://topperarg.vteximg.com.br/arquivos/ids/506944-600-600/ZAPATILLAS_LEROI_027395_1.jpg?v=639056579593470000",
        "variantes": [
            (
                "Marrón/Natural",
                [
                    ("35", 6),
                    ("36", 0),
                    ("37", 0),
                    ("38", 0),
                    ("39", 0),
                    ("40", 1),
                    ("41", 1),
                    ("42", 0),
                ],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Topper Vigo",
        "descripcion": "Silueta urbana con detalles contrastantes y plantilla acolchada.",
        "precio": Decimal("78999.00"),
        "marca": "Topper",
        "categoria": "Urbano",
        "imagen": "https://topperarg.vteximg.com.br/arquivos/ids/444453-600-600/ZAPATILLAS_VIGO_025870_1.jpg?v=638842096453700000",
        "variantes": [
            (
                "Negro",
                [
                    ("35", 5),
                    ("36", 6),
                    ("37", 0),
                    ("38", 0),
                    ("39", 1),
                    ("40", 7),
                    ("41", 8),
                    ("42", 1),
                ],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Topper Terre",
        "descripcion": "Suela con buen agarre para caminatas en terreno suelto y uso diario.",
        "precio": Decimal("62999.00"),
        "marca": "Topper",
        "categoria": "Outdoor",
        "imagen": "https://topperarg.vteximg.com.br/arquivos/ids/549405-600-600/TERRE%20BLANCO%201.jpg",
        "variantes": [
            (
                "Blanco/Gris",
                [
                    ("35", 8),
                    ("36", 0),
                    ("37", 0),
                    ("38", 0),
                    ("39", 0),
                    ("40", 2),
                    ("41", 3),
                    ("42", 4),
                ],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Topper Map Kids",
        "descripcion": "Zapatilla infantil resistente, con cordones y puntera reforzada.",
        "precio": Decimal("62999.00"),
        "marca": "Topper",
        "categoria": "Infantil",
        "imagen": "https://topperarg.vteximg.com.br/arquivos/ids/551307-600-600/ZAPATILLAS_MAP_KIDS_050750_1.jpg?v=639288035771770000",
        "variantes": [
            (
                "Negro/Blanco",
                [
                    ("25", 2),
                    ("26", 0),
                    ("27", 0),
                    ("28", 0),
                    ("29", 6),
                    ("30", 4),
                    ("31", 5),
                    ("32", 6),
                ],
            ),
        ],
    },
    {
        "nombre": "Sandalia Topper Wave",
        "descripcion": "Sandalia de verano con tiras ajustables y suela antideslizante.",
        "precio": Decimal("34999.00"),
        "marca": "Topper",
        "categoria": "Verano",
        "imagen": "https://topperarg.vteximg.com.br/arquivos/ids/547760-600-600/052703_1.jpg?v=639262169384830000",
        "variantes": [
            ("Azul/Blanco", [("36.5", 0), ("38", 4), ("39", 5), ("40", 3), ("41.5", 7), ("43", 0)]),
        ],
    },
    {
        "nombre": "Botín Topper Kaiser 4 FG",
        "descripcion": (
            "Botín de fútbol con tapones fijos para césped natural y capellada sintética."
        ),
        "precio": Decimal("52900.00"),
        "marca": "Topper",
        "categoria": "Fútbol",
        "imagen": "https://topperarg.vteximg.com.br/arquivos/ids/521511-600-600/BOTINES_KAISER_4_FG_026910_1.jpg?v=639125588463400000",
        "variantes": [
            (
                "Verde/Azul/Lima",
                [
                    ("38", 0),
                    ("39", 1),
                    ("40", 1),
                    ("41", 1),
                    ("42", 0),
                    ("43", 1),
                    ("44", 2),
                    ("45", 3),
                ],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Fila Progress Lite",
        "descripcion": "Zapatilla de training liviana, pensada para gimnasio y caminatas.",
        "precio": Decimal("84900.00"),
        "marca": "Fila",
        "categoria": "Urbano",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6917349-600-600/fila_F01TR00044_337_00.jpg?v=638930200845100000",
        "variantes": [
            ("Negro/Grafito/Rojo", [("39", 0), ("40", 7), ("41", 8), ("42", 0)]),
            (
                "Grafito/Negro/Verde lima",
                [("38", 4), ("39", 0), ("40", 0), ("41", 4), ("42", 1), ("43", 0)],
            ),
            ("Azul marino/Blanco/Rojo", [("39", 0), ("40", 6), ("41", 1), ("42", 0)]),
        ],
    },
    {
        "nombre": "Zapatilla Fila Sprint",
        "descripcion": "Perfil bajo y malla transpirable para el uso diario.",
        "precio": Decimal("79900.00"),
        "marca": "Fila",
        "categoria": "Urbano",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6942721-600-600/fila_F01TR00126_972_00.jpg?v=639237960544200000",
        "variantes": [
            ("Negro/Grafito", [("38", 2), ("39", 3), ("40", 1), ("41", 2), ("42", 3), ("43", 0)]),
            (
                "Azul marino/Azul noche",
                [
                    ("38", 0),
                    ("39", 1),
                    ("40", 7),
                    ("41", 8),
                    ("42", 1),
                    ("43", 1),
                    ("44", 1),
                    ("45", 1),
                ],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Fila Memory Sportland",
        "descripcion": "Plantilla de memoria y ajuste cómodo para llevar todo el día.",
        "precio": Decimal("89900.00"),
        "marca": "Fila",
        "categoria": "Urbano",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6941207-600-600/fila_1SR20831_001_00.jpg?v=639228379633730000",
        "variantes": [
            ("Negro", [("40", 1), ("41", 7), ("42", 8), ("43", 1), ("44", 2), ("45", 3)]),
            (
                "Blanco/Azul marino/Plata",
                [("40", 0), ("41", 5), ("42", 0), ("43", 7), ("44", 8), ("45", 1)],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Fila Decypher 98/25",
        "descripcion": "Diseño chunky de inspiración noventera con suela gruesa.",
        "precio": Decimal("99900.00"),
        "marca": "Fila",
        "categoria": "Urbano",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6933957-600-600/fila_101038_001_00.jpg?v=639141233387170000",
        "variantes": [
            ("Negro/Blanco", [("40", 5), ("41", 6), ("42", 7), ("43", 8), ("44", 1), ("45", 1)]),
            ("Gris/Beige", [("40", 0), ("41", 6), ("42", 7), ("43", 8), ("44", 1), ("45", 2)]),
            ("Blanco", [("40", 0), ("41", 7), ("42", 1), ("43", 0)]),
        ],
    },
    {
        "nombre": "Zapatilla Fila Euro Jogger Sport II",
        "descripcion": "Clásico running de los 90, hoy como zapatilla urbana.",
        "precio": Decimal("99900.00"),
        "marca": "Fila",
        "categoria": "Urbano",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6902226-600-600/fila_F01L00308_5226_00.jpg?v=638829400289970000",
        "variantes": [
            (
                "Gris/Azul marino/Rojo",
                [
                    ("38", 1),
                    ("39", 1),
                    ("40", 2),
                    ("41", 1),
                    ("42", 4),
                    ("43", 0),
                    ("44", 0),
                    ("45", 7),
                ],
            ),
            (
                "Negro/Gris/Rojo",
                [
                    ("38", 4),
                    ("39", 1),
                    ("40", 1),
                    ("41", 0),
                    ("42", 0),
                    ("43", 6),
                    ("44", 1),
                    ("45", 1),
                ],
            ),
            ("Negro/Blanco crudo/Gris", [("38", 7), ("39", 0), ("40", 6), ("41", 0)]),
        ],
    },
    {
        "nombre": "Zapatilla Fila New Retro RN",
        "descripcion": "Silueta retro con paneles de gamuza y suela de goma.",
        "precio": Decimal("119900.00"),
        "marca": "Fila",
        "categoria": "Urbano",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6941092-600-600/fila_105215_031_00.jpg?v=639228379507170000",
        "variantes": [
            (
                "Gris oscuro/Plata/Blanco",
                [("40", 0), ("41", 8), ("42", 1), ("43", 2), ("44", 3), ("45", 1)],
            ),
            (
                "Blanco/Plata/Verde agua",
                [("40", 0), ("41", 1), ("42", 2), ("43", 3), ("44", 4), ("45", 5)],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Fila Comet 2",
        "descripcion": "Running de entrenamiento diario con entresuela amortiguada.",
        "precio": Decimal("99900.00"),
        "marca": "Fila",
        "categoria": "Running",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6928833-600-600/fila_F01R00192_7158_00.jpg?v=639074680061370000",
        "variantes": [
            (
                "Negro/Naranja/Gris",
                [("38", 0), ("39", 3), ("40", 1), ("41", 1), ("42", 0), ("43", 1), ("44", 0)],
            ),
            (
                "Azul marino/Negro/Rojo oscuro",
                [
                    ("38", 1),
                    ("39", 4),
                    ("40", 2),
                    ("41", 3),
                    ("42", 4),
                    ("43", 0),
                    ("44", 0),
                    ("45", 7),
                ],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Fila Fastness",
        "descripcion": "Malla liviana y buena respuesta para correr en ciudad.",
        "precio": Decimal("89900.00"),
        "marca": "Fila",
        "categoria": "Running",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6913924-600-600/fila_F01R00193_7096_00.jpg?v=638917585417070000",
        "variantes": [
            (
                "Naranja/Azul/Blanco",
                [("39", 0), ("40", 1), ("41", 0), ("42", 0), ("43", 0), ("44", 0), ("45", 1)],
            ),
            ("Negro/Rojo oscuro/Gris", [("38", 2), ("39", 0)]),
            ("Gris claro/Azul/Negro", [("38", 5), ("39", 1), ("40", 4), ("41", 5), ("42", 0)]),
        ],
    },
    {
        "nombre": "Zapatilla Fila Racer Skytrail",
        "descripcion": "Zapatilla de trail con suela dentada para terrenos irregulares.",
        "precio": Decimal("199900.00"),
        "marca": "Fila",
        "categoria": "Outdoor",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6930504-600-600/fila_F01R00144_6764_00.jpg?v=639092911563170000",
        "variantes": [
            (
                "Verde/Azul marino/Azul cielo",
                [
                    ("38", 0),
                    ("39", 1),
                    ("40", 5),
                    ("41", 6),
                    ("42", 7),
                    ("43", 8),
                    ("44", 0),
                    ("45", 2),
                ],
            ),
            (
                "Beige/Oro/Beige piedra",
                [
                    ("38", 1),
                    ("39", 5),
                    ("40", 3),
                    ("41", 4),
                    ("42", 5),
                    ("43", 6),
                    ("44", 7),
                    ("45", 8),
                ],
            ),
        ],
    },
    {
        "nombre": "Ojota Fila Drifter Basic",
        "descripcion": "Ojota de goma, cómoda para pileta y playa.",
        "precio": Decimal("44900.00"),
        "marca": "Fila",
        "categoria": "Verano",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6955377-600-600/Name_293980.jpg?v=639280276233200000",
        "variantes": [
            (
                "Blanco/Azul marino/Rojo",
                [
                    ("37", 0),
                    ("38", 6),
                    ("39", 7),
                    ("40", 5),
                    ("41", 6),
                    ("42", 7),
                    ("43", 8),
                    ("44", 1),
                ],
            ),
            (
                "Negro/Blanco/Rojo",
                [
                    ("37", 0),
                    ("38", 8),
                    ("39", 0),
                    ("40", 7),
                    ("41", 8),
                    ("42", 1),
                    ("43", 2),
                    ("44", 3),
                ],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Fila Disruptor II Premium",
        "descripcion": "Icónica silueta chunky con suela de sierra y terminaciones premium.",
        "precio": Decimal("159900.00"),
        "marca": "Fila",
        "categoria": "Urbano",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6892474-600-600/fila_5FM00002_125_00.jpg.jpg?v=639179253756700000",
        "variantes": [
            (
                "Blanco/Azul marino/Rojo",
                [("35", 1), ("36", 2), ("37", 3), ("38", 4), ("39", 5), ("40", 0)],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Fila Sky Trail Kids",
        "descripcion": "Zapatilla infantil de outdoor liviana, con suela de buen agarre.",
        "precio": Decimal("74900.00"),
        "marca": "Fila",
        "categoria": "Infantil",
        "imagen": "https://filaar.vteximg.com.br/arquivos/ids/6940229-600-600/fila_F04K00059_7625_00.jpg?v=639214565844400000",
        "variantes": [
            (
                "Gris/Negro/Verde lima",
                [("27", 0), ("28", 1), ("29", 2), ("30", 8), ("31", 1), ("32", 1), ("33", 0)],
            ),
            (
                "Azul marino/Verde oscuro/Caramelo oscuro",
                [
                    ("27", 8),
                    ("28", 1),
                    ("29", 2),
                    ("30", 8),
                    ("31", 1),
                    ("32", 0),
                    ("33", 1),
                    ("34", 0),
                ],
            ),
            (
                "Verde hielo/Azul marino/Verde pálido",
                [
                    ("27", 6),
                    ("28", 7),
                    ("29", 8),
                    ("30", 6),
                    ("31", 7),
                    ("32", 8),
                    ("33", 1),
                    ("34", 2),
                ],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Asics Gel-Excite 10",
        "descripcion": "Running de entrenamiento con amortiguación GEL y upper de malla.",
        "precio": Decimal("249900.00"),
        "marca": "Asics",
        "categoria": "Running",
        "imagen": "https://asicsar.vteximg.com.br/arquivos/ids/190313-600-600/asics_1011B600405_405_00.jpg?v=638920992860670000",
        "variantes": [
            ("Turquesa", [("42", 0), ("42.5", 3), ("43", 0)]),
        ],
    },
    {
        "nombre": "Zapatilla Asics Gel-Sparta 2",
        "descripcion": "Running versátil para entrenamiento diario, con calce estable.",
        "precio": Decimal("189900.00"),
        "marca": "Asics",
        "categoria": "Running",
        "imagen": "https://asicsar.vteximg.com.br/arquivos/ids/190913-600-600/asics_1011B815404_404_00.jpg?v=638930314976600000",
        "variantes": [
            ("Azul", [("42", 0), ("43", 5), ("44", 6), ("45", 0)]),
        ],
    },
    {
        "nombre": "Zapatilla Asics Gel-Equation 14",
        "descripcion": "Amortiguación suave y pisada neutra para kilómetros urbanos.",
        "precio": Decimal("189900.00"),
        "marca": "Asics",
        "categoria": "Running",
        "imagen": "https://asicsar.vteximg.com.br/arquivos/ids/189504-600-600/asics_1011C113020_020_00.jpg?v=638906183390300000",
        "variantes": [
            ("Gris", [("42", 0), ("43", 6), ("44", 7), ("45", 0)]),
        ],
    },
    {
        "nombre": "Zapatilla Asics Novablast 5",
        "descripcion": "Entresuela de espuma reactiva para rodadas rápidas y cómodas.",
        "precio": Decimal("339900.00"),
        "marca": "Asics",
        "categoria": "Running",
        "imagen": "https://asicsar.vteximg.com.br/arquivos/ids/209197-600-600/asics_1012B765402_402_00.jpg?v=639202454174900000",
        "variantes": [
            ("Verde", [("35.5", 3), ("36", 0)]),
        ],
    },
    {
        "nombre": "Zapatilla Asics Gel-Nyc 2055",
        "descripcion": "Silueta sportstyle con capas de malla y gamuza.",
        "precio": Decimal("339900.00"),
        "marca": "Asics",
        "categoria": "Urbano",
        "imagen": "https://asicsar.vteximg.com.br/arquivos/ids/188315-600-600/asics_1203A542102_102_00.jpg?v=638901964441330000",
        "variantes": [
            ("Crema", [("43", 0), ("43.5", 5), ("44", 0)]),
        ],
    },
    {
        "nombre": "Zapatilla Asics Japan S",
        "descripcion": "Clásico de perfil bajo con capellada de cuero y suela de goma.",
        "precio": Decimal("219900.00"),
        "marca": "Asics",
        "categoria": "Urbano",
        "imagen": "https://asicsar.vteximg.com.br/arquivos/ids/187697-600-600/asics_1202A118134_134_00.jpg?v=638890727640130000",
        "variantes": [
            ("Blanco", [("36", 4), ("37", 0), ("38", 0), ("38.5", 7), ("39", 0)]),
        ],
    },
    {
        "nombre": "Zapatilla Asics Gel-Lyte V",
        "descripcion": "Icónico runner de los 90 con ajuste envolvente y paneles de color.",
        "precio": Decimal("299900.00"),
        "marca": "Asics",
        "categoria": "Urbano",
        "imagen": "https://asicsar.vteximg.com.br/arquivos/ids/168744-600-600/asics_1203A344100_100_00.jpg?v=638793688678070000",
        "variantes": [
            ("Blanco", [("39", 0), ("40", 3), ("40.5", 6), ("41", 0)]),
        ],
    },
    {
        "nombre": "Zapatilla Asics Metafuji Trail",
        "descripcion": "Trail de competición con tracción agresiva en barro y roca.",
        "precio": Decimal("439900.00"),
        "marca": "Asics",
        "categoria": "Outdoor",
        "imagen": "https://asicsar.vteximg.com.br/arquivos/ids/195471-600-600/asics_1013A141100_100_00.jpg?v=639003656744900000",
        "variantes": [
            ("Crema", [("39", 0), ("40", 3), ("40.5", 3), ("41", 0)]),
        ],
    },
    {
        "nombre": "Botín Asics Lethal Flash IT FF 3",
        "descripcion": "Botín de rugby y fútbol con tapones fijos y calce seguro.",
        "precio": Decimal("299900.00"),
        "marca": "Asics",
        "categoria": "Fútbol",
        "imagen": "https://asicsar.vteximg.com.br/arquivos/ids/180993-600-600/asics_1111A256100_100_00.jpg?v=638810058701730000",
        "variantes": [
            (
                "Blanco",
                [
                    ("40", 7),
                    ("40.5", 5),
                    ("41", 8),
                    ("42", 1),
                    ("42.5", 5),
                    ("43", 2),
                    ("44", 3),
                    ("45", 1),
                ],
            ),
        ],
    },
    {
        "nombre": "Zapatilla Asics Gel-Resolution X Padel",
        "descripcion": "Zapatilla de pádel con soporte lateral y suela para cemento.",
        "precio": Decimal("349900.00"),
        "marca": "Asics",
        "categoria": "Tenis",
        "imagen": "https://asicsar.vteximg.com.br/arquivos/ids/197736-600-600/asics_1042A285400_400_00.jpg?v=639039938160100000",
        "variantes": [
            ("Celeste", [("40", 0), ("40.5", 5), ("41", 6)]),
        ],
    },
]


def _admin_credentials() -> tuple[str, str]:
    email = os.getenv("ADMIN_EMAIL", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "").strip()
    if not email or not password:
        raise RuntimeError(
            "Faltan ADMIN_EMAIL y ADMIN_PASSWORD en .env. Copialos de .env.example "
            "y volve a correr el seed (D-013)."
        )
    return email, password


def seed_admin() -> bool:
    """Create the bootstrap admin if it does not exist."""
    email, password = _admin_credentials()
    try:
        creado = crear_admin_si_no_existe(email=email, password=password, nombre=ADMIN_NOMBRE)
    except ErrorDeRegistro as error:
        print(f"[error] admin: {error}")
        return False

    if creado:
        print(f"[ok]   admin creado: {email}")
    else:
        print(f"[skip] admin ya existe: {email}")
    return creado


def _obtener_categoria(session: Session, nombre: str) -> Categoria:
    categoria = session.exec(select(Categoria).where(Categoria.nombre == nombre)).one_or_none()
    if categoria is not None:
        return categoria

    categoria = Categoria(nombre=nombre)
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria


def seed_categorias() -> int:
    """Create the catalog categories if they do not exist."""
    creadas = 0
    with get_session() as session:
        existentes = {c.nombre for c in session.exec(select(Categoria)).all()}
        for nombre in CATEGORIAS:
            if nombre in existentes:
                continue
            _obtener_categoria(session, nombre)
            creadas += 1

    print(f"[ok]   categorias nuevas: {creadas}")
    return creadas


def seed_productos() -> int:
    """Create the demo catalog with its variants if it does not exist."""
    creados = 0
    with get_session() as session:
        for data in PRODUCTOS:
            existente = session.exec(
                select(Producto).where(
                    Producto.nombre == data["nombre"],
                    Producto.marca == data["marca"],
                )
            ).first()
            if existente is not None:
                print(f"[skip] producto ya existe: {data['nombre']}")
                continue

            categoria = _obtener_categoria(session, data["categoria"])
            producto = Producto(
                nombre=data["nombre"],
                descripcion=data["descripcion"],
                precio=data["precio"],
                marca=data["marca"],
                categoria_id=categoria.id,
                imagen=data["imagen"],
            )
            session.add(producto)
            session.commit()
            session.refresh(producto)

            for color, talles in data["variantes"]:
                for talle, cantidad in talles:
                    session.add(
                        Stocks(
                            producto_id=producto.id,
                            color=color,
                            talle=talle,
                            cantidad_disponible=cantidad,
                        )
                    )
            session.commit()

            creados += 1
            print(f"[ok]   producto creado: {producto.nombre} (id={producto.id})")

    return creados


def main() -> None:
    print("--- Seed inicial ---")
    seed_admin()
    seed_categorias()
    creados = seed_productos()
    print("--------------------")
    print(f"Productos nuevos: {creados}")


if __name__ == "__main__":
    main()
