import pytest

from slugify import slugify


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Hola Mundo", "hola-mundo"),
        ("  espacios   al   principio y al final  ", "espacios-al-principio-y-al-final"),
        ("Canción del pirata", "cancion-del-pirata"),
        ("Año nuevo, vida nueva", "ano-nuevo-vida-nueva"),
        ("Pingüino & Cía.", "pinguino-cia"),
        ("¿Qué tal? ¡Muy bien!", "que-tal-muy-bien"),
        ("C++ vs. C#", "c-vs-c"),
        ("versión 2.0.3", "version-2-0-3"),
        ("ya-tiene--guiones---", "ya-tiene-guiones"),
        ("MAYÚSCULAS Y minúsculas", "mayusculas-y-minusculas"),
        ("", ""),
        ("!!!", ""),
    ],
)
def test_slugify(text, expected):
    assert slugify(text) == expected


def test_max_length_cuts_at_word_boundary():
    text = "el experimento del cuaderno del doctor falken con modelos gratuitos"
    result = slugify(text, max_length=30)
    assert result == "el-experimento-del-cuaderno"
    assert len(result) <= 30


def test_max_length_long_first_word():
    assert slugify("supercalifragilisticoespialidoso", max_length=10) == "supercalif"


def test_max_length_exact_fit():
    assert slugify("hola mundo", max_length=10) == "hola-mundo"
