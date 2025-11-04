"""Funciones centralizadas de monitoreo y healthchecks."""

from __future__ import annotations

import os
import subprocess
import time
from typing import Any, Callable, Dict, Tuple

import django
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

try:
    from rest_framework import __version__ as drf_version  # type: ignore
except Exception:  # pragma: no cover - fallback por si DRF no está instalado
    drf_version = "desconocido"

try:
    from rag_system.vector_store.chroma_manager import ChromaManager
except Exception:  # pragma: no cover - se maneja en cada check
    ChromaManager = None  # type: ignore

try:
    from rag_system.drive_sync.drive_manager import GoogleDriveManager
except Exception:  # pragma: no cover - se maneja en cada check
    GoogleDriveManager = None  # type: ignore


CheckResult = Tuple[bool, Dict[str, Any]]


def _run_check(fn: Callable[[], CheckResult]) -> Dict[str, Any]:
    """Ejecuta un check capturando excepciones y midiendo latencia."""
    start = time.perf_counter()
    ok: bool
    details: Dict[str, Any]

    try:
        ok, details = fn()
    except Exception as exc:  # pragma: no cover - validamos en tests
        ok = False
        details = {"error": str(exc)}

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    details = details or {}
    details.setdefault("latency_ms", elapsed_ms)
    return {"ok": bool(ok), "details": details}


def _safe_dependency_version(module: str) -> str:
    try:
        mod = __import__(module)
    except Exception:
        return "desconocido"

    return getattr(mod, "__version__", "desconocido") or "desconocido"


def _get_git_commit() -> str:
    """Obtiene el hash corto del commit actual."""
    if os.getenv("BUILD_SHA"):
        return os.getenv("BUILD_SHA", "desconocido")[:8]

    try:
        commit = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
        return commit or "desconocido"
    except Exception:
        return "desconocido"


def get_build_metadata() -> Dict[str, Any]:
    """Devuelve información del build y dependencias clave."""
    return {
        "version": getattr(settings, "APP_VERSION", "1.0.0"),
        "environment": "production" if not settings.DEBUG else "development",
        "commit": _get_git_commit(),
        "build_time": os.getenv("BUILD_TIMESTAMP", "desconocido"),
        "dependencies": {
            "django": django.get_version(),
            "djangorestframework": drf_version,
            "chromadb": _safe_dependency_version("chromadb"),
            "langchain": _safe_dependency_version("langchain"),
            "sentence_transformers": _safe_dependency_version("sentence_transformers"),
        },
    }


def check_api() -> CheckResult:
    """Confirma que la capa web esté lista."""
    return True, {
        "django_version": django.get_version(),
        "debug": settings.DEBUG,
    }


def check_database() -> CheckResult:
    """Ejecuta una consulta de salud contra la base de datos por defecto."""
    alias = "default"
    try:
        with connections[alias].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except OperationalError as exc:
        return False, {
            "engine": connections[alias].settings_dict.get("ENGINE", "desconocido"),
            "error": str(exc),
        }

    return True, {
        "engine": connections[alias].settings_dict.get("ENGINE", "desconocido"),
    }


def check_vector_store() -> CheckResult:
    """Valida la disponibilidad de ChromaDB y obtiene estadísticas básicas."""
    if ChromaManager is None:
        return False, {"error": "ChromaManager no disponible"}

    manager = ChromaManager()
    is_ready = manager.is_ready()
    stats = manager.get_collection_stats() if is_ready else {}
    minimal_stats = {
        key: stats.get(key)
        for key in ("collection_name", "total_documents", "persist_directory")
        if isinstance(stats, dict)
    }
    return is_ready, minimal_stats


def check_worker() -> CheckResult:
    """Verifica el estado del worker de sincronización (Google Drive)."""
    if GoogleDriveManager is None:
        return False, {"error": "GoogleDriveManager no disponible"}

    manager = GoogleDriveManager()
    authenticated = manager.is_authenticated()
    status = manager.get_sync_status()
    status_summary = {
        "authenticated": authenticated,
        "folder_id": status.get("folder_id"),
        "local_files_count": status.get("local_files_count"),
    }
    return authenticated, status_summary


SERVICE_REGISTRY: Dict[str, Callable[[], Dict[str, Any]]] = {
    "api": lambda: _run_check(check_api),
    "database": lambda: _run_check(check_database),
    "worker": lambda: _run_check(check_worker),
    "vector_db": lambda: _run_check(check_vector_store),
}


def collect_health_checks() -> Dict[str, Dict[str, Any]]:
    """Ejecuta todos los healthchecks registrados."""
    results: Dict[str, Dict[str, Any]] = {}
    for name, fn in SERVICE_REGISTRY.items():
        results[name] = fn()
    return results


def overall_status(services: Dict[str, Dict[str, Any]]) -> str:
    """Retorna el estado agregado del sistema."""
    if all(entry.get("ok", False) for entry in services.values()):
        return "healthy"
    if any(entry.get("ok", False) for entry in services.values()):
        return "degraded"
    return "down"
