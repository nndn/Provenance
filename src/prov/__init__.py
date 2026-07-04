"""Provenance CLI — spec-driven development."""

__all__ = ["main"]


def __getattr__(name: str):
    if name == "main":
        from prov.cli import main

        return main
    raise AttributeError(name)
