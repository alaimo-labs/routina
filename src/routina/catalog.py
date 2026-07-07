"""Catálogo local de ejercicios con vocabulario cerrado.

El catálogo vive en `catalog/exercises_v1.json` (versionado en el repo) y comparte
enums con el perfil del usuario (equipment, injuries): eso permite cruzar
perfil ↔ ejercicios de forma verificable mecánicamente en los evals.

La estructura y los IDs son en inglés; los contenidos (nombres de ejercicios,
labels del vocabulario, notas) son bilingües: `{"es": ..., "en": ...}`.
`localized()` resuelve un ejercicio a un solo idioma para el modelo o la UI.
"""

import json
from functools import lru_cache
from typing import Any

from .config import CATALOG_PATH

LEVEL_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def vocab() -> dict[str, Any]:
    """Vocabulario cerrado del catálogo (para la UI del perfil y validaciones)."""
    cat = load_catalog()
    return {
        "equipment": cat["equipment"],
        "injuries": cat["injuries"],
        "muscle_groups": cat["muscle_groups"],
        "levels": cat["levels"],
    }


def valid_ids(key: str) -> set[str]:
    """IDs válidos de un vocabulario ('equipment' | 'injuries' | 'muscle_groups')."""
    return {item["id"] for item in load_catalog()[key]}


def localized(exercise: dict[str, Any], lang: str) -> dict[str, Any]:
    """Resuelve los campos bilingües de un ejercicio a un solo idioma."""
    out = dict(exercise)
    out["name"] = exercise["name"].get(lang) or exercise["name"]["es"]
    out["notes"] = exercise["notes"].get(lang) or exercise["notes"]["es"]
    return out


def search(
    *,
    muscle_group: str | None = None,
    level: str | None = None,
    available_equipment: list[str] | None = None,
    avoid_injuries: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Filtra el catálogo.

    - `muscle_group`: el ejercicio debe trabajar ese grupo muscular.
    - `level`: nivel del usuario; se incluyen ejercicios de ese nivel o inferior.
    - `available_equipment`: el ejercicio solo entra si TODO su equipamiento
      requerido está disponible (lista vacía = no requiere nada, siempre entra).
      `None` = no filtrar por equipamiento.
    - `avoid_injuries`: se excluyen ejercicios contraindicados para alguna de ellas.
    """
    results = []
    for ex in load_catalog()["exercises"]:
        if muscle_group and muscle_group not in ex["muscle_groups"]:
            continue
        if level and LEVEL_ORDER[ex["level"]] > LEVEL_ORDER[level]:
            continue
        if available_equipment is not None and not set(ex["equipment"]) <= set(
            available_equipment
        ):
            continue
        if avoid_injuries and set(ex["contraindicated_for"]) & set(avoid_injuries):
            continue
        results.append(ex)
    return results
