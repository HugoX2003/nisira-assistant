"""Herramientas para generar evidencia del RN-004 Escalabilidad.

Se ejecuta dentro de ``manage.py shell`` para producir métricas reales de carga
contra los endpoints RAG. Genera archivos dentro de este mismo directorio.
"""
from __future__ import annotations

import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

try:  # Opcional: estado del sistema RAG
    from rag_system.rag_engine.pipeline import RAGPipeline  # type: ignore
    RAG_AVAILABLE = True
except Exception:  # pragma: no cover - defensivo
    RAGPipeline = None  # type: ignore
    RAG_AVAILABLE = False

OUTPUT_DIR = Path(__file__).resolve().parent
DOCS_DIR = Path(__file__).resolve().parents[2] / "data" / "documents"
RESULTS_JSON = OUTPUT_DIR / "scalability_results.json"
RESULTS_CSV = OUTPUT_DIR / "scalability_results.csv"
MERMAID_DATA = OUTPUT_DIR / "latency_by_concurrency.json"
USER_USERNAME = "scalability_tester"
USER_PASSWORD = "EscalaR@pida2024"


@dataclass
class ScenarioResult:
    name: str
    concurrent_users: int
    requests_per_user: int
    use_rag: bool
    total_requests: int
    successful_requests: int
    failed_requests: int
    mean_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    max_latency_ms: float
    min_latency_ms: float

    def to_csv_row(self) -> str:
        return (
            f"{self.name},{self.concurrent_users},{self.requests_per_user},{self.use_rag},"
            f"{self.total_requests},{self.successful_requests},{self.failed_requests},"
            f"{self.mean_latency_ms:.2f},{self.median_latency_ms:.2f},{self.p95_latency_ms:.2f},"
            f"{self.max_latency_ms:.2f},{self.min_latency_ms:.2f}"
        )


def percentile(values: List[float], pct: float) -> float:
    """Calcular percentil sin depender de numpy."""
    if not values:
        return 0.0
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * pct
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return values_sorted[int(k)]
    d0 = values_sorted[f] * (c - k)
    d1 = values_sorted[c] * (k - f)
    return d0 + d1


def ensure_test_user() -> Any:
    """Crear o actualizar el usuario usado en las pruebas."""
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username=USER_USERNAME,
        defaults={
            "email": "scalabilidad@example.com",
            "is_staff": True,
        },
    )
    user.set_password(USER_PASSWORD)
    if not user.first_name:
        user.first_name = "Tester"
    if not user.last_name:
        user.last_name = "Escalabilidad"
    user.save()
    return user


def create_authenticated_client() -> APIClient:
    """Crear un APIClient autenticado por fuerza (sin depender de JWT)."""
    user = ensure_test_user()
    client = APIClient()
    client.defaults["HTTP_HOST"] = "localhost"
    client.force_authenticate(user=user)
    return client


def perform_single_request(use_rag: bool, message_idx: int) -> Dict[str, Any]:
    client = create_authenticated_client()
    payload = {
        "content": f"Mensaje de prueba #{message_idx} sobre escalabilidad.",
        "use_rag": use_rag,
    }
    start = time.perf_counter()
    response = client.post("/api/rag/chat/", payload, format="json")
    elapsed_ms = (time.perf_counter() - start) * 1000
    body: Dict[str, Any]
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.content.decode("utf-8", errors="ignore")}
    return {
        "status_code": response.status_code,
        "latency_ms": elapsed_ms,
        "rag_used": body.get("rag_used"),
        "timestamp": timezone.now().isoformat(),
        "body": body,
    }


def run_load_scenario(name: str, concurrent_users: int, requests_per_user: int, use_rag: bool) -> ScenarioResult:
    """Ejecuta un escenario de carga concurrente."""
    total_requests = concurrent_users * requests_per_user
    latencies: List[float] = []
    successes = 0
    failures = 0

    def worker(worker_id: int) -> List[Dict[str, Any]]:
        results = []
        for req in range(requests_per_user):
            result = perform_single_request(use_rag=use_rag, message_idx=worker_id * requests_per_user + req)
            results.append(result)
        return results

    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(worker, idx) for idx in range(concurrent_users)]
        for future in as_completed(futures):
            for result in future.result():
                latencies.append(result["latency_ms"])
                if result["status_code"] == 201:
                    successes += 1
                else:
                    failures += 1

    if not latencies:
        latencies = [0.0]

    return ScenarioResult(
        name=name,
        concurrent_users=concurrent_users,
        requests_per_user=requests_per_user,
        use_rag=use_rag,
        total_requests=total_requests,
        successful_requests=successes,
        failed_requests=failures,
        mean_latency_ms=statistics.mean(latencies),
        median_latency_ms=statistics.median(latencies),
        p95_latency_ms=percentile(latencies, 0.95),
        max_latency_ms=max(latencies),
        min_latency_ms=min(latencies),
    )


def collect_rag_status() -> Dict[str, Any]:
    client = create_authenticated_client()
    response = client.get("/api/rag/system-status/")
    try:
        data = response.json()
    except Exception:
        data = {"status_code": response.status_code, "raw": response.content.decode("utf-8", errors="ignore")}
    data["http_status"] = response.status_code
    return data


def collect_pipeline_metrics() -> Dict[str, Any]:
    if not RAG_AVAILABLE:
        return {"available": False, "reason": "RAGPipeline no importable"}
    try:
        pipeline = RAGPipeline()
        status = pipeline.get_system_status()
    except Exception as exc:  # pragma: no cover - dependencias externas
        return {"available": False, "reason": str(exc)}
    return {"available": True, "status": status}


def count_documents() -> Dict[str, Any]:
    if not DOCS_DIR.exists():
        return {"path": str(DOCS_DIR), "exists": False, "total_files": 0, "pdf_files": 0}
    pdf_files = [f for f in DOCS_DIR.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]
    all_files = [f for f in DOCS_DIR.iterdir() if f.is_file()]
    return {
        "path": str(DOCS_DIR),
        "exists": True,
        "total_files": len(all_files),
        "pdf_files": len(pdf_files),
    }


def export_results(results: List[ScenarioResult], context: Dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": timezone.now().isoformat(),
        "document_inventory": count_documents(),
        "rag_status": context.get("rag_status"),
        "pipeline_status": context.get("pipeline_status"),
        "scenarios": [asdict(result) for result in results],
    }

    RESULTS_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    csv_header = (
        "name,concurrent_users,requests_per_user,use_rag,total_requests,successful_requests," \
        "failed_requests,mean_latency_ms,median_latency_ms,p95_latency_ms,max_latency_ms,min_latency_ms"
    )
    csv_rows = [csv_header] + [result.to_csv_row() for result in results]
    RESULTS_CSV.write_text("\n".join(csv_rows), encoding="utf-8")

    mermaid_data = {
        result.name: {
            "concurrency": result.concurrent_users,
            "p95_latency_ms": result.p95_latency_ms,
            "mean_latency_ms": result.mean_latency_ms,
        }
        for result in results
    }
    MERMAID_DATA.write_text(json.dumps(mermaid_data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    scenarios: List[ScenarioResult] = []

    rag_status = collect_rag_status()
    pipeline_status = collect_pipeline_metrics()

    scenarios.append(run_load_scenario("baseline_chat_conc_5", concurrent_users=5, requests_per_user=4, use_rag=False))
    scenarios.append(run_load_scenario("baseline_chat_conc_10", concurrent_users=10, requests_per_user=4, use_rag=False))
    scenarios.append(run_load_scenario("rag_toggle_conc_6", concurrent_users=6, requests_per_user=3, use_rag=True))

    export_results(scenarios, {"rag_status": rag_status, "pipeline_status": pipeline_status})


if __name__ == "__main__":  # pragma: no cover
    main()
