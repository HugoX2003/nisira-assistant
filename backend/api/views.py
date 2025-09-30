"""
API Views para el sistema de chat básico
========================================

Sistema de chat simple con Django REST Framework
- Autenticación JWT
- Manejo de conversaciones
- Envío de mensajes
- API REST estándar
"""

import logging
from datetime import datetime

# Django & DRF imports
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

# Local imports
from .models import Conversation, Message

# Configuración de logging
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint de verificación de salud del sistema
    """
    return Response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'message': 'API funcionando correctamente'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    """
    Obtener todas las conversaciones del usuario autenticado
    """
    try:
        conversations = Conversation.objects.filter(user=request.user).order_by('-created_at')
        
        conversation_data = []
        for conv in conversations:
            last_message = conv.messages.last()
            conversation_data.append({
                'id': conv.id,
                'title': conv.title,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'last_message': {
                    'content': last_message.content[:100] + '...' if last_message and len(last_message.content) > 100 else last_message.content if last_message else '',
                    'timestamp': last_message.timestamp.isoformat() if last_message else None
                } if last_message else None
            })
        
        return Response({
            'conversations': conversation_data,
            'count': len(conversation_data)
        })
        
    except Exception as e:
        logger.error(f"Error al obtener conversaciones: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_conversation(request):
    """
    Crear una nueva conversación
    """
    try:
        title = request.data.get('title', f'Conversación {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        
        conversation = Conversation.objects.create(
            user=request.user,
            title=title
        )
        
        return Response({
            'id': conversation.id,
            'title': conversation.title,
            'created_at': conversation.created_at.isoformat(),
            'message': 'Conversación creada exitosamente'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error al crear conversación: {str(e)}")
        return Response(
            {'error': 'Error al crear la conversación'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, conversation_id):
    """
    Obtener todos los mensajes de una conversación específica
    """
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        messages = conversation.messages.all().order_by('timestamp')
        
        message_data = []
        for msg in messages:
            message_data.append({
                'id': msg.id,
                'content': msg.content,
                'is_user': msg.is_user,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return Response({
            'conversation_id': conversation.id,
            'conversation_title': conversation.title,
            'messages': message_data,
            'count': len(message_data)
        })
        
    except Conversation.DoesNotExist:
        return Response(
            {'error': 'Conversación no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al obtener mensajes: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """
    Enviar un mensaje y generar respuesta básica
    """
    try:
        conversation_id = request.data.get('conversation_id')
        content = request.data.get('content', '').strip()
        
        if not content:
            return Response(
                {'error': 'El mensaje no puede estar vacío'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not conversation_id:
            return Response(
                {'error': 'ID de conversación requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que la conversación existe y pertenece al usuario
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversación no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Crear mensaje del usuario
        user_message = Message.objects.create(
            conversation=conversation,
            content=content,
            is_user=True
        )
        
        # Generar respuesta básica del asistente
        assistant_response = generate_basic_response(content)
        
        # Crear mensaje del asistente
        assistant_message = Message.objects.create(
            conversation=conversation,
            content=assistant_response,
            is_user=False
        )
        
        # Actualizar timestamp de la conversación
        conversation.updated_at = datetime.now()
        conversation.save()
        
        return Response({
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'is_user': user_message.is_user,
                'timestamp': user_message.timestamp.isoformat()
            },
            'assistant_message': {
                'id': assistant_message.id,
                'content': assistant_message.content,
                'is_user': assistant_message.is_user,
                'timestamp': assistant_message.timestamp.isoformat()
            },
            'conversation_id': conversation.id
        })
        
    except Exception as e:
        logger.error(f"Error al enviar mensaje: {str(e)}")
        return Response(
            {'error': 'Error al procesar el mensaje'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def generate_basic_response(user_message: str) -> str:
    """
    Genera una respuesta básica del asistente
    Esta función puede ser reemplazada con un sistema más avanzado más adelante
    """
    user_message_lower = user_message.lower()
    
    # Respuestas predefinidas básicas
    if any(greeting in user_message_lower for greeting in ['hola', 'hello', 'hi', 'buenos días', 'buenas tardes']):
        return "¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?"
    
    elif any(thanks in user_message_lower for thanks in ['gracias', 'thank you', 'thanks']):
        return "¡De nada! Estoy aquí para ayudarte en lo que necesites."
    
    elif any(goodbye in user_message_lower for goodbye in ['adiós', 'bye', 'hasta luego', 'chau']):
        return "¡Hasta luego! Que tengas un excelente día."
    
    elif '?' in user_message:
        return f"Es una pregunta interesante. Basándome en tu consulta sobre '{user_message[:50]}...', te puedo decir que este es un tema que requiere análisis. En el futuro, cuando integre capacidades más avanzadas, podré darte respuestas más detalladas."
    
    else:
        return f"Entiendo que me comentas sobre '{user_message[:50]}...'. Actualmente soy un asistente básico, pero estoy aquí para ayudarte. ¿Hay algo específico en lo que pueda asistirte?"


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_conversation(request, conversation_id):
    """
    Eliminar una conversación específica
    """
    try:
        conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        conversation.delete()
        
        return Response({
            'message': 'Conversación eliminada exitosamente'
        })
        
    except Conversation.DoesNotExist:
        return Response(
            {'error': 'Conversación no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error al eliminar conversación: {str(e)}")
        return Response(
            {'error': 'Error al eliminar la conversación'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """
    Información general de la API
    """
    return Response({
        'name': 'Nisira Assistant API',
        'version': '1.0.0',
        'description': 'API REST para sistema de chat básico',
        'endpoints': {
            'health': '/api/health/',
            'conversations': '/api/conversations/',
            'messages': '/api/conversations/{id}/messages/',
            'send_message': '/api/chat/',
            'api_info': '/api/info/'
        },
        'authentication': 'JWT Token required for most endpoints'
    })