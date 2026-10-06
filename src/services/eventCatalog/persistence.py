"""Persistencia atomica del estado operativo y sus versiones nombradas."""

import json
import os
from pathlib import Path


class JsonStateRepository:
    """Lee y guarda un unico documento JSON mediante reemplazo atomico."""

    def __init__(self, path):
        self._path = Path(path)

    def load(self):
        if not self._path.exists():
            return {"state": None, "history": [], "versions": []}
        try:
            with self._path.open("r", encoding="utf-8") as state_file:
                document = json.load(state_file)
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"No se pudo leer el estado persistido: {error}") from error
        if document.get("schema_version") != 1:
            raise RuntimeError("La version del archivo de estado no es compatible.")
        return document

    def save(self, document):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._path.with_suffix(self._path.suffix + ".tmp")
        try:
            with temporary_path.open("w", encoding="utf-8", newline="\n") as state_file:
                json.dump(document, state_file, ensure_ascii=False, separators=(",", ":"))
                state_file.flush()
                os.fsync(state_file.fileno())
            os.replace(temporary_path, self._path)
        except OSError as error:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise RuntimeError(f"No se pudo guardar el estado persistido: {error}") from error
