"""Convierte textos en slugs para URLs."""


def slugify(text: str, max_length: int = 50) -> str:
    """Devuelve un slug en minúsculas, sin acentos, con palabras separadas por guiones.

    - Quita acentos y diacríticos (á → a, ñ → n, ü → u).
    - Cualquier secuencia de caracteres que no sean letras o dígitos se convierte en un único guion.
    - Sin guiones al principio ni al final.
    - Como mucho `max_length` caracteres, cortando en un límite de palabra (sin dejar un guion final).
      Si la primera palabra ya supera `max_length`, se corta a `max_length` caracteres.
    - Si no queda nada, devuelve una cadena vacía.
    """
    raise NotImplementedError
