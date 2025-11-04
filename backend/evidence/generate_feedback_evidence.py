import json
from pathlib import Path

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from api.models import Conversation, Message, Rating, ExperimentRun

BASE_DIR = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = Path(__file__).resolve().parent

# Ensure evidence user exists and is staff
user, created = User.objects.get_or_create(
    username="evidence_tester",
    defaults={
        "email": "evidence@example.com",
    },
)
updated_fields = []
if created or not user.has_usable_password():
    user.set_password("evidence123")
    updated_fields.append("password")

if not user.is_staff:
    user.is_staff = True
    updated_fields.append("is_staff")

if updated_fields:
    user.save(update_fields=updated_fields)

# Seed conversation, message, and rating
conversation, _ = Conversation.objects.get_or_create(
    user=user,
    title="Evidencia Feedback",
)

bot_message, _ = Message.objects.get_or_create(
    conversation=conversation,
    sender="bot",
    defaults={"text": "Respuesta de prueba para evidencia."},
)
if not bot_message.text:
    bot_message.text = "Respuesta de prueba para evidencia."
    bot_message.save(update_fields=["text"])

Rating.objects.update_or_create(
    message=bot_message,
    user=user,
    defaults={
        "value": Rating.RatingValue.LIKE,
        "comment": "Feedback positivo de evidencia",
        "issue_tag": Rating.IssueTag.IRRELEVANT,
        "updated_at": timezone.now(),
    },
)

# Seed experiment run for guardrail status if none exists
if not ExperimentRun.objects.exists():
    ExperimentRun.objects.create(
        name="Exp Evidencia",
        variant_name="v1",
        executed_by="evidence_tester",
        notes="Evidencia de guardrails",
        baseline_precision=0.70,
        variant_precision=0.78,
        baseline_faithfulness=0.72,
        variant_faithfulness=0.75,
        baseline_latency=1.2,
        variant_latency=1.0,
    )

# Use DRF test client to hit real endpoints
client = APIClient()
client.force_authenticate(user=user)
client.defaults['HTTP_HOST'] = 'localhost'

summary_response = client.get("/api/ratings/summary/")
export_json_response = client.get("/api/ratings/export/", {"export_format": "json"})
export_csv_response = client.get("/api/ratings/export/", {"export_format": "csv"})

guardrail_response = client.get("/api/guardrails/status/")

debug_statuses = {
    "rating_summary": summary_response.status_code,
    "ratings_export_json": export_json_response.status_code,
    "ratings_export_csv": export_csv_response.status_code,
    "guardrail_status": guardrail_response.status_code,
}

for name, status_code in debug_statuses.items():
    print(f"{name}: {status_code}")

for name, resp in {
    "rating_summary": summary_response,
    "ratings_export_json": export_json_response,
    "ratings_export_csv": export_csv_response,
    "guardrail_status": guardrail_response,
}.items():
    if resp.status_code != 200:
        raise SystemExit(f"❌ La llamada a {name} falló con status {resp.status_code}: {getattr(resp, 'data', resp.content)}")

EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

(summary_path := EVIDENCE_DIR / "rating_summary.json").write_text(
    json.dumps(summary_response.json(), indent=2),
    encoding="utf-8",
)
(export_json_path := EVIDENCE_DIR / "ratings_export.json").write_text(
    json.dumps(export_json_response.json(), indent=2),
    encoding="utf-8",
)
(export_csv_path := EVIDENCE_DIR / "ratings_export.csv").write_bytes(export_csv_response.content)
(guardrail_path := EVIDENCE_DIR / "guardrail_status.json").write_text(
    json.dumps(guardrail_response.json(), indent=2),
    encoding="utf-8",
)

print(f"✅ Evidencias generadas:\n- {summary_path}\n- {export_json_path}\n- {export_csv_path}\n- {guardrail_path}")
