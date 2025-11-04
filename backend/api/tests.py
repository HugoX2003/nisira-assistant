from unittest import mock

from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from monitoring import health
from api.models import Conversation, Message, Rating, RatingFeedbackEvent


class ServiceStatusEndpointTests(APITestCase):
	def test_status_endpoint_returns_service_matrix(self):
		response = self.client.get(reverse("service_status"))

		self.assertEqual(response.status_code, 200)
		payload = response.json()

		self.assertIn("services", payload)
		for expected_key in {"api", "database", "worker", "vector_db"}:
			self.assertIn(expected_key, payload["services"])
			self.assertIn("ok", payload["services"][expected_key])

		self.assertIn(payload["status"], {"healthy", "degraded", "down"})

	@mock.patch("api.views.collect_health_checks")
	def test_status_endpoint_handles_degraded_services(self, mocked_collect):
		mocked_collect.return_value = {
			"api": {"ok": True, "details": {}},
			"database": {"ok": True, "details": {}},
			"worker": {"ok": False, "details": {"error": "simulado"}},
			"vector_db": {"ok": True, "details": {}},
		}

		response = self.client.get(reverse("service_status"))

		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["status"], "degraded")
		self.assertFalse(payload["services"]["worker"]["ok"])
		self.assertEqual(payload["services"]["worker"]["details"].get("error"), "simulado")


class ChaosHealthChecksTests(SimpleTestCase):
	def test_collect_health_checks_handles_vector_db_failure(self):
		with mock.patch("monitoring.health.check_vector_store", side_effect=RuntimeError("fallo vector")):
			results = health.collect_health_checks()

		vector_result = results["vector_db"]
		self.assertFalse(vector_result["ok"])
		self.assertIn("fallo vector", vector_result["details"].get("error", ""))

	def test_collect_health_checks_handles_db_failure(self):
		with mock.patch("monitoring.health.check_database", side_effect=RuntimeError("db caida")):
			results = health.collect_health_checks()

		db_result = results["database"]
		self.assertFalse(db_result["ok"])
		self.assertIn("db caida", db_result["details"].get("error", ""))

	def test_overall_status_states(self):
		all_good = {"api": {"ok": True}, "database": {"ok": True}}
		degraded = {"api": {"ok": True}, "database": {"ok": False}}
		all_down = {"api": {"ok": False}, "database": {"ok": False}}

		self.assertEqual(health.overall_status(all_good), "healthy")
		self.assertEqual(health.overall_status(degraded), "degraded")
		self.assertEqual(health.overall_status(all_down), "down")


class RatingEndpointsTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="tester", password="secret")
		self.other_user = User.objects.create_user(username="other", password="secret")
		self.conversation = Conversation.objects.create(user=self.user, title="Demo")
		self.bot_message = Message.objects.create(
			conversation=self.conversation,
			sender="bot",
			text="Respuesta generada",
		)
		self.client.force_authenticate(self.user)

	def test_user_can_submit_like_rating(self):
		response = self.client.post(reverse("submit_rating"), {
			"message_id": self.bot_message.id,
			"value": "like",
		})
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertEqual(payload["value"], "like")
		self.assertEqual(Rating.objects.count(), 1)
		self.assertEqual(RatingFeedbackEvent.objects.count(), 1)
		self.assertEqual(RatingFeedbackEvent.objects.first().status, RatingFeedbackEvent.Status.COMPLETED)

	def test_rating_is_idempotent(self):
		for _ in range(2):
			self.client.post(reverse("submit_rating"), {
				"message_id": self.bot_message.id,
				"value": "like",
			})
		self.assertEqual(Rating.objects.count(), 1)
		self.assertEqual(Rating.objects.first().value, "like")

	def test_user_can_toggle_rating(self):
		self.client.post(reverse("submit_rating"), {
			"message_id": self.bot_message.id,
			"value": "dislike",
		})
		self.assertEqual(Rating.objects.filter(message=self.bot_message, user=self.user).count(), 1)

		self.client.post(reverse("submit_rating"), {
			"message_id": self.bot_message.id,
			"value": "clear",
		})
		self.assertFalse(Rating.objects.filter(message=self.bot_message, user=self.user).exists())

	def test_cannot_rate_other_users_message(self):
		foreign_conversation = Conversation.objects.create(user=self.other_user, title="Ajena")
		foreign_message = Message.objects.create(conversation=foreign_conversation, sender="bot", text="Otro")
		response = self.client.post(reverse("submit_rating"), {
			"message_id": foreign_message.id,
			"value": "like",
		})
		self.assertEqual(response.status_code, 404)

	def test_cannot_rate_user_messages(self):
		user_message = Message.objects.create(conversation=self.conversation, sender="user", text="Hola")
		response = self.client.post(reverse("submit_rating"), {
			"message_id": user_message.id,
			"value": "like",
		})
		self.assertEqual(response.status_code, 400)

	def test_summary_requires_staff(self):
		Rating.objects.create(message=self.bot_message, user=self.user, value=Rating.RatingValue.LIKE)
		response = self.client.get(reverse("rating_summary"))
		self.assertEqual(response.status_code, 403)

		self.user.is_staff = True
		self.user.save(update_fields=["is_staff"])
		response = self.client.get(reverse("rating_summary"))
		self.assertEqual(response.status_code, 200)
		payload = response.json()
		self.assertIn("total", payload)
		self.assertEqual(payload["likes"], 1)

	def test_export_requires_staff(self):
		Rating.objects.create(message=self.bot_message, user=self.user, value=Rating.RatingValue.LIKE)
		response = self.client.get(reverse("export_ratings"))
		self.assertEqual(response.status_code, 403)

		self.user.is_staff = True
		self.user.save(update_fields=["is_staff"])
		self.assertEqual(reverse("export_ratings"), "/api/ratings/export/")
		response = self.client.get(f"{reverse('export_ratings')}?export_format=json")
		self.assertEqual(response.status_code, 200, response.content.decode())
		payload = response.json()
		self.assertEqual(payload["count"], 1)

		response_csv = self.client.get(f"{reverse('export_ratings')}?export_format=csv")
		self.assertEqual(response_csv.status_code, 200, response_csv.content.decode())
		self.assertEqual(response_csv["Content-Type"], "text/csv; charset=utf-8")


