"""Cache JSON em disco com gravação atômica."""

import json
import os
import tempfile
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / "cache"


def caminho(prefixo, lat, lon):
    return PASTA / f"{prefixo}_{lat:.2f}_{lon:.2f}.json"


def ler(path):
    """Devolve o JSON do arquivo, ou None se ele não existe ou é inválido."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def gravar(path, dados):
    """Grava num temporário da mesma pasta e troca com os.replace: nunca deixa arquivo parcial."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(dados, f)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise
