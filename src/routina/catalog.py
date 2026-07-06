"""Catálogo local de ejercicios con vocabulario cerrado.

El catálogo vive en `catalog/ejercicios_v1.json` (versionado en el repo) y comparte
enums con el perfil del usuario (equipamiento, lesiones): eso permite cruzar
perfil ↔ ejercicios de forma verificable mecánicamente en los evals.
"""

import json
from functools import lru_cache
from typing import Any

from .config import CATALOG_PATH

NIVEL_ORDEN = {"principiante": 0, "intermedio": 1, "avanzado": 2}


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def vocab() -> dict[str, Any]:
    """Vocabulario cerrado del catálogo (para la UI del perfil y validaciones)."""
    cat = load_catalog()
    return {
        "equipamiento": cat["equipamiento"],
        "lesiones": cat["lesiones"],
        "grupos_musculares": cat["grupos_musculares"],
        "niveles": cat["niveles"],
    }


def valid_ids(key: str) -> set[str]:
    """IDs válidos de un vocabulario ('equipamiento' | 'lesiones' | 'grupos_musculares')."""
    return {item["id"] for item in load_catalog()[key]}


def search(
    *,
    grupo: str | None = None,
    nivel: str | None = None,
    equipamiento_disponible: list[str] | None = None,
    evitar_lesiones: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Filtra el catálogo.

    - `grupo`: el ejercicio debe trabajar ese grupo muscular.
    - `nivel`: nivel del usuario; se incluyen ejercicios de ese nivel o inferior.
    - `equipamiento_disponible`: el ejercicio solo entra si TODO su equipamiento
      requerido está disponible (lista vacía = no requiere nada, siempre entra).
      `None` = no filtrar por equipamiento.
    - `evitar_lesiones`: se excluyen ejercicios contraindicados para alguna de ellas.
    """
    resultados = []
    for ej in load_catalog()["ejercicios"]:
        if grupo and grupo not in ej["grupos"]:
            continue
        if nivel and NIVEL_ORDEN[ej["nivel"]] > NIVEL_ORDEN[nivel]:
            continue
        if equipamiento_disponible is not None and not set(ej["equipamiento"]) <= set(
            equipamiento_disponible
        ):
            continue
        if evitar_lesiones and set(ej["contraindicado_para"]) & set(evitar_lesiones):
            continue
        resultados.append(ej)
    return resultados
