"""Static files."""


def locate_dir() -> str:
    """Return path to static files."""
    return __path__[0]
