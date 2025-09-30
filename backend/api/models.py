# Modelos para guardar el historial de chat
from django.db import models
from django.contrib.auth.models import User

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
    # Fecha de creación del mensaje
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ordena los mensajes por fecha de creación (de más antiguo a más nuevo)
        ordering = ['created_at']

    def __str__(self):
        # Muestra el tipo de remitente y los primeros 40 caracteres del mensaje
        return f"{self.sender}: {self.text[:40]}"

