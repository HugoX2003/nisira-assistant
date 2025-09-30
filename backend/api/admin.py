# administración y revisión de los historiales de chat nativo de django admin
from django.contrib import admin
from .models import Conversation, Message

# Configuración de la vista para el modelo Conversation en el admin
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    # Campos que se muestran en la lista
    list_display = ("id", "user", "title", "created_at", "updated_at")
    # Permite buscar por título y usuario
    search_fields = ("title", "user__username")

# Configuración de la vista para el modelo Message en el admin
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    # Campos que se muestran en la lista
    list_display = ("id", "conversation", "sender", "created_at")
    # Permite filtrar por tipo de remitente (user/bot)
    list_filter = ("sender",)
    # Permite buscar por texto del mensaje
    search_fields = ("text",)

