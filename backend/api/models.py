# Modelos para guardar el historial de chat
from django.db import models
from django.contrib.auth.models import User
import json
from django.utils import timezone

# Representa una conversación de chat entre el usuario y el asistente
class Conversation(models.Model):
    # Usuario dueño de la conversación
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='conversations')
    # Título de la conversación (puede ser la primera pregunta)
    title = models.CharField(max_length=255, blank=True, default='')
    # Fecha de creación
    created_at = models.DateTimeField(auto_now_add=True)
    # Fecha de última actualización
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Ordena las conversaciones por la fecha de actualización más reciente
        ordering = ['-updated_at']

    def __str__(self):
        # Muestra el título o el ID si no hay título
        return self.title or f"Conversation {self.pk}"

# Representa un mensaje individual dentro de una conversación
class Message(models.Model):
    # Indica si el mensaje es del usuario o del bot
    SENDER_CHOICES = (
        ('user', 'User'),
        ('bot', 'Bot'),
    )
    # Relación con la conversación a la que pertenece
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    # Quién envió el mensaje (user/bot)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    # Texto del mensaje
    text = models.TextField()
    # Fuentes RAG (solo para mensajes del bot)
    sources_json = models.TextField(blank=True, null=True, help_text="JSON con las fuentes RAG utilizadas")
    # Fecha de creación del mensaje
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ordena los mensajes por fecha de creación (de más antiguo a más nuevo)
        ordering = ['created_at']

    def __str__(self):
        # Muestra el tipo de remitente y los primeros 40 caracteres del mensaje
        return f"{self.sender}: {self.text[:40]}"

    @property
    def sources(self):
        """Devuelve las fuentes deserializadas como lista"""
        if self.sources_json:
            try:
                return json.loads(self.sources_json)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def set_sources(self, sources_list):
        """Guarda las fuentes como JSON"""
        if sources_list:
            self.sources_json = json.dumps(sources_list, ensure_ascii=False)
        else:
            self.sources_json = None


class Rating(models.Model):
    class RatingValue(models.TextChoices):
        LIKE = "like", "Like"
        DISLIKE = "dislike", "Dislike"

    class IssueTag(models.TextChoices):
        NONE = "none", "Sin etiqueta"
        IRRELEVANT = "irrelevante", "Irrelevante"
        NO_EVIDENCE = "sin_evidencia", "Sin evidencia"
        LATE = "tardio", "Tardío"
        HALLUCINATION = "alucinacion", "Alucinación"
        ACTION_ERROR = "accion_incorrecta", "Acción incorrecta"
        OTHER = "otro", "Otro"

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    value = models.CharField(max_length=7, choices=RatingValue.choices)
    comment = models.CharField(max_length=500, blank=True)
    issue_tag = models.CharField(
        max_length=32,
        choices=IssueTag.choices,
        default=IssueTag.NONE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user"],
                name="unique_rating_per_user_and_message",
            )
        ]
        indexes = [
            models.Index(fields=["message", "user"]),
            models.Index(fields=["updated_at"]),
            models.Index(fields=["issue_tag"]),
        ]

    def __str__(self):
        return f"Rating({self.user_id}->{self.message_id}:{self.value})"


class RatingFeedbackEvent(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    rating = models.ForeignKey(
        Rating,
        on_delete=models.CASCADE,
        related_name="events",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reason = models.CharField(max_length=64, default="user-submitted")
    attempts = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["updated_at"]),
        ]

    def mark_pending(self):
        self.status = self.Status.PENDING
        self.error_message = ""
        self.last_attempt_at = None
        self.completed_at = None
        self.attempts = 0
        self.save(update_fields=[
            "status",
            "error_message",
            "last_attempt_at",
            "completed_at",
            "attempts",
            "updated_at",
        ])

    def mark_completed(self):
        self.status = self.Status.COMPLETED
        self.error_message = ""
        self.completed_at = timezone.now()
        self.last_attempt_at = self.completed_at
        self.attempts += 1
        self.save(update_fields=[
            "status",
            "error_message",
            "completed_at",
            "last_attempt_at",
            "attempts",
            "updated_at",
        ])

    def mark_failed(self, error_message: str):
        self.status = self.Status.FAILED
        self.error_message = error_message[:500]
        self.last_attempt_at = timezone.now()
        self.attempts += 1
        self.save(update_fields=[
            "status",
            "error_message",
            "last_attempt_at",
            "attempts",
            "updated_at",
        ])


class ExperimentRun(models.Model):
    name = models.CharField(max_length=120)
    variant_name = models.CharField(max_length=120)
    executed_by = models.CharField(max_length=120)
    notes = models.TextField(blank=True)

    baseline_precision = models.FloatField()
    variant_precision = models.FloatField()
    baseline_faithfulness = models.FloatField()
    variant_faithfulness = models.FloatField()
    baseline_latency = models.FloatField(help_text="Latency en segundos")
    variant_latency = models.FloatField(help_text="Latency en segundos")

    delta_precision = models.FloatField(editable=False)
    delta_faithfulness = models.FloatField(editable=False)
    delta_latency = models.FloatField(editable=False)

    guardrail_passed = models.BooleanField(default=True)
    guardrail_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["guardrail_passed"]),
        ]

    def save(self, *args, **kwargs):
        self.delta_precision = self.variant_precision - self.baseline_precision
        self.delta_faithfulness = self.variant_faithfulness - self.baseline_faithfulness
        self.delta_latency = self.variant_latency - self.baseline_latency
        super().save(*args, **kwargs)

    def __str__(self):
        status = "OK" if self.guardrail_passed else "BLOCKED"
        return f"ExperimentRun({self.name}:{self.variant_name} - {status})"


class QueryMetrics(models.Model):
    """
    Modelo para almacenar métricas de cada consulta realizada al sistema RAG
    Usado para análisis de rendimiento y tesis
    """
    # Identificación
    query_id = models.CharField(max_length=100, unique=True, help_text="UUID de la consulta")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Texto de la consulta
    query_text = models.TextField()
    
    # Métricas de Rendimiento (Performance)
    total_latency = models.FloatField(help_text="Tiempo total de respuesta en segundos")
    time_to_first_token = models.FloatField(help_text="Tiempo hasta el primer token en segundos")
    retrieval_time = models.FloatField(help_text="Tiempo de recuperación de documentos en segundos")
    generation_time = models.FloatField(help_text="Tiempo de generación de respuesta en segundos")
    
    # Clasificación de complejidad
    is_complex_query = models.BooleanField(default=False, help_text="Si es una consulta compleja")
    query_complexity_score = models.FloatField(null=True, blank=True, help_text="Score de complejidad 0-1")
    
    # Métricas de Recuperación
    documents_retrieved = models.IntegerField(help_text="Número de documentos recuperados")
    top_k = models.IntegerField(default=5, help_text="Valor de K usado")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_complex_query']),
        ]
    
    def __str__(self):
        return f"QueryMetrics({self.query_id[:8]}... - {self.total_latency:.2f}s)"


class RAGASMetrics(models.Model):
    """
    Modelo para almacenar métricas de precisión y exactitud del sistema RAG
    Calculadas usando un evaluador personalizado (sin dependencias externas)
    """
    # Identificación del batch de evaluación
    evaluation_id = models.CharField(max_length=100, unique=True)
    query_metrics = models.ForeignKey(QueryMetrics, on_delete=models.CASCADE, null=True, blank=True)
    
    # Texto de la consulta y respuesta evaluada
    query_text = models.TextField(blank=True, default='')
    response_text = models.TextField(blank=True, default='')
    retrieved_contexts = models.TextField(blank=True, default='', help_text="JSON con contextos recuperados")
    
    # Métricas de precisión (calculadas con sistema personalizado)
    precision_at_k = models.FloatField(default=0.0, help_text="Precision@k score (0-1)")
    recall_at_k = models.FloatField(default=0.0, help_text="Recall@k score (0-1)")
    faithfulness_score = models.FloatField(default=0.0, help_text="Faithfulness score (0-1)")
    answer_relevancy = models.FloatField(default=0.0, help_text="Answer relevancy score (0-1)")
    context_precision = models.FloatField(null=True, blank=True)
    context_recall = models.FloatField(null=True, blank=True)
    
    # Tasa de alucinación (inversa de faithfulness)
    hallucination_rate = models.FloatField(default=0.0, help_text="Tasa de alucinación (0-1)")
    
    # Word Error Rate (cuando hay ground truth disponible)
    wer_score = models.FloatField(null=True, blank=True, help_text="Word Error Rate - menor es mejor")
    
    # Metadata
    k_value = models.IntegerField(default=5, help_text="Valor de K usado en la evaluación")
    evaluation_timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-evaluation_timestamp']
        indexes = [
            models.Index(fields=['evaluation_timestamp']),
        ]
    
    def save(self, *args, **kwargs):
        # Calcular hallucination_rate como inversa de faithfulness
        self.hallucination_rate = 1.0 - self.faithfulness_score
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"PrecisionMetrics({self.evaluation_id[:8]}... - F:{self.faithfulness_score:.2f}, P@k:{self.precision_at_k:.2f})"

