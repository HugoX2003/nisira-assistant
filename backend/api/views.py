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
import csv
from io import StringIO

# Django & DRF imports
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import HttpResponse, Http404
from django.conf import settings
import os
import mimetypes
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

# Local imports
from .models import Conversation, Message, Rating, RatingFeedbackEvent, ExperimentRun
from .serializers import (
    RatingRequestSerializer,
    RatingSerializer,
    ExperimentRunCreateSerializer,
    ExperimentRunSerializer,
)
from monitoring.health import collect_health_checks, get_build_metadata, overall_status

# Configuración de logging
logger = logging.getLogger(__name__)


# ============================================================================
# VISTA DE BIENVENIDA / HOME
# ============================================================================

@api_view(["GET"])
@permission_classes([AllowAny])
def home_view(request):
    """
    Vista de bienvenida para la raíz de la API.
    Muestra información básica sobre los endpoints disponibles.
    """
    return Response({
        "message": "Bienvenido a NISIRA Assistant API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health/",
            "api_info": "/info/",
            "authentication": {
                "login": "/auth/login/",
                "register": "/auth/register/",
                "token": "/auth/token/",
            },
            "rag_system": {
                "status": "/rag/status/",
                "query": "/rag/query/",
                "chat": "/rag/chat/",
            },
            "admin": "/admin/",
            "swagger": "/api/schema/swagger-ui/",
        },
        "documentation": "https://github.com/HugoX2003/nisira-assistant",
    })


# ============================================================================
# VISTAS BÁSICAS DE SALUD Y ESTADO
# ============================================================================


# RAG System imports
try:
    import sys
    import os
    from django.conf import settings
    
    # Agregar rag_system al path
    rag_path = os.path.join(settings.BASE_DIR, 'rag_system')
    if rag_path not in sys.path:
        sys.path.append(rag_path)
    
    from rag_system.rag_engine.pipeline import RAGPipeline
    RAG_MODULES_AVAILABLE = True
    logger.info("✅ Sistema RAG importado correctamente")
except ImportError as e:
    RAG_MODULES_AVAILABLE = False
    RAGPipeline = None
    logger.warning(f"⚠️ Sistema RAG no disponible: {e}")


def calculate_adaptive_top_k(question: str) -> int:
    """
    Calcula dinámicamente el número de documentos a recuperar basado en:
    - Longitud de la consulta
    - Complejidad detectada (palabras clave)
    - Número de preguntas
    
    Rangos:
    - Consultas simples (< 50 chars): 3-5 docs
    - Consultas medias (50-150 chars): 5-8 docs
    - Consultas complejas (> 150 chars): 8-12 docs
    - Con múltiples preguntas: +2 docs por cada "?"
    """
    # Base según longitud
    length = len(question)
    
    if length < 50:
        base_k = 3
    elif length < 100:
        base_k = 5
    elif length < 150:
        base_k = 7
    else:
        base_k = 9
    
    # Bonus por múltiples preguntas
    question_marks = question.count('?')
    if question_marks > 1:
        base_k += min((question_marks - 1) * 2, 4)  # Máximo +4 por preguntas múltiples
    
    # Bonus por palabras clave complejas
    complex_keywords = ['comparar', 'diferencia', 'analizar', 'explicar detalladamente', 
                       'por qué', 'cómo funciona', 'implementar', 'relacionan']
    keyword_count = sum(1 for kw in complex_keywords if kw in question.lower())
    if keyword_count > 0:
        base_k += min(keyword_count, 3)  # Máximo +3 por keywords
    
    # Limitar a rango razonable
    top_k = max(3, min(base_k, 15))
    
    return top_k


def process_rating_event(event: RatingFeedbackEvent) -> RatingFeedbackEvent:
    """Procesa un evento de calificación y maneja reintentos básicos."""
    event.attempts += 1
    event.last_attempt_at = timezone.now()

    try:
        logger.info(
            "📨 Procesando evento de calificación %s (rating=%s, intento=%s)",
            event.pk,
            event.rating_id,
            event.attempts,
        )
        # Aquí se integraría el envío a sistemas externos/telemetría.
        event.status = RatingFeedbackEvent.Status.COMPLETED
        event.completed_at = event.last_attempt_at
        event.error_message = ""
    except Exception as exc:  # pragma: no cover (bloque defensivo)
        logger.exception("Error procesando evento de calificación %s", event.pk)
        event.status = RatingFeedbackEvent.Status.FAILED
        event.error_message = str(exc)[:500]

    event.save(
        update_fields=[
            "status",
            "attempts",
            "last_attempt_at",
            "completed_at",
            "error_message",
            "updated_at",
        ]
    )
    return event


def enqueue_rating_event(rating: Rating, reason: str = "user-submitted") -> RatingFeedbackEvent:
    event = RatingFeedbackEvent.objects.create(
        rating=rating,
        reason=reason,
        status=RatingFeedbackEvent.Status.PENDING,
    )
    return process_rating_event(event)


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


@api_view(['POST'])
@permission_classes([AllowAny])
def custom_login(request):
    """
    Vista de login personalizada que devuelve información del usuario junto con los tokens
    """
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Validaciones específicas con mensajes claros
        if not username and not password:
            return Response(
                {'error': 'Por favor ingresa tu usuario y contraseña'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not username:
            return Response(
                {'error': 'Por favor ingresa tu nombre de usuario'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not password:
            return Response(
                {'error': 'Por favor ingresa tu contraseña'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si el usuario existe
        try:
            existing_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'El usuario no existe. Verifica tu nombre de usuario o regístrate'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Autenticar usuario (verifica contraseña)
        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {'error': 'Contraseña incorrecta. Intenta nuevamente'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verificar si el usuario está activo
        if not user.is_active:
            return Response(
                {'error': 'Tu cuenta está desactivada. Contacta al administrador'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generar tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Respuesta con tokens e información del usuario
        return Response({
            'access': str(access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=status.HTTP_200_OK)

    except Exception as exc:  # pragma: no cover (manejo defensivo)
        logger.exception("Error inesperado en custom_login")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def serve_document(request, filename: str):
    """Servir documentos almacenados en BD (PostgreSQL) o directorio (filesystem)."""
    from .models import UploadedDocument
    
    # Primero buscar en la base de datos
    try:
        uploaded_doc = UploadedDocument.objects.get(file_name=filename)
        file_path = uploaded_doc.file_path
        
        # Verificar si está en PostgreSQL o filesystem
        if file_path.startswith('postgres://'):
            # Archivo en PostgreSQL - obtener desde PostgresFileStore
            file_uuid = file_path.replace('postgres://', '')
            
            try:
                from rag_system.storage.postgres_file_store import PostgresFileStore
                file_store = PostgresFileStore()
                
                file_data = file_store.get_file(file_uuid)
                
                if not file_data:
                    raise Http404('Documento no encontrado en PostgreSQL')
                
                content_type = file_data.get('mime_type', 'application/octet-stream')
                file_content = file_data.get('content')
                
                response = HttpResponse(file_content, content_type=content_type)
                response['Content-Disposition'] = f'inline; filename="{filename}"'
                return response
                
            except Exception as e:
                logger.error(f"Error obteniendo archivo de PostgreSQL {file_uuid}: {str(e)}")
                raise Http404('Error al obtener documento de PostgreSQL')
        else:
            # Archivo en filesystem - verificar que existe
            if not os.path.exists(file_path):
                logger.warning(f"Archivo en BD pero no en disco: {file_path}")
                raise Http404('Documento no encontrado en el sistema de archivos')
            
            content_type, _ = mimetypes.guess_type(file_path)
            content_type = content_type or 'application/octet-stream'
            
            try:
                with open(file_path, 'rb') as file_handle:
                    response = HttpResponse(file_handle.read(), content_type=content_type)
                    response['Content-Disposition'] = f'inline; filename="{filename}"'
                    return response
            except Exception as e:
                logger.error(f"Error leyendo archivo {file_path}: {str(e)}")
                raise Http404('Error al leer el documento')
            
    except UploadedDocument.DoesNotExist:
        # Intentar buscar directamente en PostgreSQL (para archivos sincronizados antes del fix)
        try:
            from rag_system.storage.postgres_file_store import PostgresFileStore
            file_store = PostgresFileStore()
            file_data = file_store.get_file(file_name=filename)
            
            if file_data:
                logger.info(f"✅ Documento encontrado directamente en PostgreSQL: {filename}")
                content_type = file_data.get('mime_type', 'application/octet-stream')
                
                response = HttpResponse(file_data['file_content'], content_type=content_type)
                response['Content-Disposition'] = f'inline; filename="{filename}"'
                return response
        except Exception as e:
            logger.warning(f"No se encontró en PostgreSQL directo: {e}")

        # Fallback: buscar en el directorio legacy
        base_path = getattr(settings, 'DOCUMENTS_ROOT', os.path.join(settings.BASE_DIR, 'data', 'documents'))
        file_path = os.path.join(base_path, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"Documento no encontrado en ninguna parte: {filename}")
            raise Http404('Documento no encontrado')

        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or 'application/octet-stream'

        try:
            with open(file_path, 'rb') as file_handle:
                response = HttpResponse(file_handle.read(), content_type=content_type)
                response['Content-Disposition'] = f'inline; filename="{filename}"'
                return response
        except Exception as e:
            logger.error(f"Error leyendo archivo legacy {file_path}: {str(e)}")
            raise Http404('Error al leer el documento')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    """Listar conversaciones del usuario autenticado."""
    try:
        conversations = (
            Conversation.objects.filter(user=request.user)
            .order_by('-updated_at')
            .values('id', 'title', 'created_at', 'updated_at')
        )

        results = [
            {
                'id': entry['id'],
                'title': entry['title'],
                'created_at': entry['created_at'].isoformat() if entry['created_at'] else None,
                'updated_at': entry['updated_at'].isoformat() if entry['updated_at'] else None,
            }
            for entry in conversations
        ]

        return Response({'count': len(results), 'conversations': results})
    except Exception as exc:  # pragma: no cover (defensivo)
        logger.exception("Error obteniendo conversaciones")
        return Response(
            {'error': 'Error al obtener las conversaciones'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        messages = conversation.messages.all().order_by('created_at')
        rating_map = {
            rating.message_id: rating
            for rating in Rating.objects.filter(
                message_id__in=messages.values_list('id', flat=True),
                user=request.user,
            )
        }
        
        message_data = []
        for msg in messages:
            message_data.append({
                'id': msg.id,
                'content': msg.text,
                'is_user': msg.sender == 'user',
                'timestamp': msg.created_at.isoformat(),
                'sources': msg.sources,
                'rating': rating_map.get(msg.id).value if rating_map.get(msg.id) else None,
                'rating_issue_tag': rating_map.get(msg.id).issue_tag if rating_map.get(msg.id) else None,
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
            text=content,
            sender='user'
        )
        
        # Generar respuesta básica del asistente
        assistant_response = generate_basic_response(content)
        
        # Crear mensaje del asistente
        assistant_message = Message.objects.create(
            conversation=conversation,
            text=assistant_response,
            sender='bot'
        )
        
        # Actualizar timestamp de la conversación
        conversation.updated_at = datetime.now()
        conversation.save()
        
        return Response({
            'user_message': {
                'id': user_message.id,
                'content': user_message.text,
                'is_user': True,
                'timestamp': user_message.created_at.isoformat(),
                'rating': None,
                'rating_issue_tag': Rating.IssueTag.NONE,
            },
            'assistant_message': {
                'id': assistant_message.id,
                'content': assistant_message.text,
                'is_user': False,
                'timestamp': assistant_message.created_at.isoformat(),
                'rating': None,
                'rating_issue_tag': Rating.IssueTag.NONE,
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
        'description': 'API REST para sistema de chat con RAG',
        'endpoints': {
            'health': '/api/health/',
            'conversations': '/api/conversations/',
            'messages': '/api/conversations/{id}/messages/',
            'send_message': '/api/chat/',
            'rag_status': '/api/rag/status/',
            'rag_sync': '/api/rag/sync/',
            'rag_query': '/api/rag/query/',
            'api_info': '/api/info/'
        },
        'authentication': 'JWT Token required for most endpoints',
        'rag_available': RAG_MODULES_AVAILABLE
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def service_status(request):
    """Estado consolidado de los servicios principales."""
    services = collect_health_checks()

    return Response({
        'status': overall_status(services),
        'timestamp': datetime.now().isoformat(),
        'services': services,
        'build': get_build_metadata(),
        'uptime_slo_target': 0.95,
    })


# ================================
# CALIFICACIONES DE RESPUESTAS
# ================================


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_rating(request):
    """Registrar o actualizar una calificación de un mensaje del asistente."""
    serializer = RatingRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data

    message_id = payload['message_id']
    value = payload['value']
    comment = payload.get('comment', '').strip()
    issue_tag = payload.get('issue_tag', Rating.IssueTag.NONE)

    try:
        message = Message.objects.select_related('conversation').get(
            id=message_id,
            conversation__user=request.user,
        )
    except Message.DoesNotExist:
        return Response(
            {'error': 'Mensaje no encontrado o sin permiso.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if message.sender != 'bot':
        return Response(
            {'error': 'Solo se pueden calificar respuestas del asistente.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if issue_tag == 'auto':
        lowered = comment.lower()
        if any(keyword in lowered for keyword in ['irrelev', 'fuera de contexto']):
            issue_tag = Rating.IssueTag.IRRELEVANT
        elif any(keyword in lowered for keyword in ['sin fuente', 'sin evidencia', 'no cites']):
            issue_tag = Rating.IssueTag.NO_EVIDENCE
        elif any(keyword in lowered for keyword in ['tard', 'lento', 'demor']):
            issue_tag = Rating.IssueTag.LATE
        elif any(keyword in lowered for keyword in ['alucina', 'invent', 'incorrecto', 'falso']):
            issue_tag = Rating.IssueTag.HALLUCINATION
        else:
            issue_tag = Rating.IssueTag.OTHER

    queue_event = None
    rating_instance = None
    action = 'noop'

    with transaction.atomic():
        if value == 'clear':
            deleted = Rating.objects.filter(message=message, user=request.user)
            deleted_count = deleted.count()
            if deleted_count:
                deleted.delete()
                action = 'removed'
            else:
                action = 'noop'
        else:
            rating_instance, created = Rating.objects.update_or_create(
                message=message,
                user=request.user,
                defaults={
                    'value': value,
                    'comment': comment,
                    'issue_tag': issue_tag,
                },
            )
            action = 'created' if created else 'updated'
            queue_event = enqueue_rating_event(rating_instance)

    response_payload = {
        'message_id': message.id,
        'conversation_id': message.conversation_id,
        'value': rating_instance.value if rating_instance else None,
        'status': action,
        'updated_at': (
            rating_instance.updated_at.isoformat()
            if rating_instance
            else timezone.now().isoformat()
        ),
        'issue_tag': rating_instance.issue_tag if rating_instance else Rating.IssueTag.NONE,
    }

    if queue_event:
        response_payload['queue_event'] = {
            'id': queue_event.id,
            'status': queue_event.status,
            'attempts': queue_event.attempts,
            'last_attempt_at': queue_event.last_attempt_at.isoformat()
            if queue_event.last_attempt_at
            else None,
        }

    return Response(response_payload)


def _build_rating_summary() -> dict:
    total = Rating.objects.count()
    likes = Rating.objects.filter(value=Rating.RatingValue.LIKE).count()
    dislikes = Rating.objects.filter(value=Rating.RatingValue.DISLIKE).count()
    net_score = likes - dislikes
    satisfaction = (likes / total) if total else 0
    last_update = (
        Rating.objects.order_by('-updated_at').values_list('updated_at', flat=True).first()
    )

    issue_breakdown = {
        entry['issue_tag']: entry['count']
        for entry in Rating.objects.values('issue_tag').annotate(count=Count('id'))
    }

    daily_breakdown_qs = (
        Rating.objects.annotate(day=TruncDate('updated_at'))
        .values('day')
        .annotate(
            total=Count('id'),
            likes=Count('id', filter=Q(value=Rating.RatingValue.LIKE)),
            dislikes=Count('id', filter=Q(value=Rating.RatingValue.DISLIKE)),
        )
        .order_by('-day')[:14]
    )

    recent_feedback = [
        {
            'id': rating.id,
            'message_id': rating.message_id,
            'conversation_id': rating.message.conversation_id,
            'value': rating.value,
            'comment': rating.comment,
            'issue_tag': rating.issue_tag,
            'updated_at': rating.updated_at.isoformat(),
            'username': rating.user.username,
        }
        for rating in Rating.objects.select_related('message__conversation', 'user')
        .order_by('-updated_at')[:10]
    ]

    queue_metrics = RatingFeedbackEvent.objects.aggregate(
        pending=Count('id', filter=Q(status=RatingFeedbackEvent.Status.PENDING)),
        failed=Count('id', filter=Q(status=RatingFeedbackEvent.Status.FAILED)),
        processed=Count('id', filter=Q(status=RatingFeedbackEvent.Status.COMPLETED)),
    )

    latest_experiment = ExperimentRun.objects.first()

    return {
        'total': total,
        'likes': likes,
        'dislikes': dislikes,
        'net_score': net_score,
        'satisfaction_rate': satisfaction,
        'last_updated': last_update.isoformat() if last_update else None,
        'issue_breakdown': issue_breakdown,
        'daily_breakdown': [
            {
                'date': entry['day'].isoformat() if entry['day'] else None,
                'total': entry['total'],
                'likes': entry['likes'],
                'dislikes': entry['dislikes'],
            }
            for entry in daily_breakdown_qs
        ],
        'recent_feedback': recent_feedback,
        'queue': {
            'pending': queue_metrics.get('pending') or 0,
            'failed': queue_metrics.get('failed') or 0,
            'processed': queue_metrics.get('processed') or 0,
        },
        'latest_experiment': ExperimentRunSerializer(latest_experiment).data if latest_experiment else None,
        'generated_at': timezone.now().isoformat(),
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rating_summary(request):
    """Resumen agregado de calificaciones para paneles internos."""
    if not request.user.is_staff:
        return Response(
            {'error': 'Acceso restringido al personal autorizado.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    data = _build_rating_summary()
    data['export_url'] = request.build_absolute_uri('/api/ratings/export/')
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_ratings(request):
    """Exportar calificaciones a CSV o JSON."""
    if not request.user.is_staff:
        return Response(
            {'error': 'Acceso restringido al personal autorizado.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    export_format = request.query_params.get('export_format', 'json').lower()
    ratings = Rating.objects.select_related('message__conversation', 'user').order_by('-updated_at')

    if export_format == 'csv':
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            'rating_id',
            'message_id',
            'conversation_id',
            'username',
            'value',
            'issue_tag',
            'comment',
            'updated_at',
        ])
        for rating in ratings:
            writer.writerow([
                rating.id,
                rating.message_id,
                rating.message.conversation_id if rating.message else None,
                rating.user.username if rating.user_id else None,
                rating.value,
                rating.issue_tag,
                rating.comment or '',
                rating.updated_at.isoformat(),
            ])

        filename = f"ratings_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    if export_format == 'json':
        serializer = RatingSerializer(ratings, many=True)
        data = serializer.data
        return Response({'count': len(data), 'results': data})

    return Response(
        {'error': 'Formato no soportado. Usa csv o json.'},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_experiment_run(request):
    if not request.user.is_staff:
        return Response(
            {'error': 'Acceso restringido al personal autorizado.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = ExperimentRunCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    with transaction.atomic():
        experiment = serializer.save()

    return Response(ExperimentRunSerializer(experiment).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_experiments(request):
    if not request.user.is_staff:
        return Response(
            {'error': 'Acceso restringido al personal autorizado.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    total_count = ExperimentRun.objects.count()
    limit_param = request.query_params.get('limit')
    queryset = ExperimentRun.objects.all()
    if limit_param:
        try:
            limit_value = int(limit_param)
            if limit_value > 0:
                queryset = queryset[:limit_value]
        except ValueError:
            return Response(
                {'error': 'El parámetro limit debe ser un entero positivo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    serializer = ExperimentRunSerializer(queryset, many=True)
    return Response({'count': total_count, 'results': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def latest_experiment(request):
    if not request.user.is_staff:
        return Response(
            {'error': 'Acceso restringido al personal autorizado.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    experiment = ExperimentRun.objects.first()
    if not experiment:
        return Response({'detail': 'Sin experimentos registrados.'}, status=status.HTTP_404_NOT_FOUND)

    return Response(ExperimentRunSerializer(experiment).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def guardrail_status(request):
    if not request.user.is_staff:
        return Response(
            {'error': 'Acceso restringido al personal autorizado.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    summary = _build_rating_summary()
    latest_experiment = ExperimentRun.objects.first()

    guardrail_passed = True
    messages = []

    if latest_experiment:
        if not latest_experiment.guardrail_passed:
            guardrail_passed = False
            messages.append(latest_experiment.guardrail_reason or 'Último experimento bloqueado por guardrails.')
    else:
        messages.append('No hay experimentos registrados aún.')

    failed_events = summary['queue']['failed']
    if failed_events:
        guardrail_passed = False
        messages.append(f'{failed_events} eventos de feedback fallidos requieren revisión.')

    threshold = request.query_params.get('satisfaction_threshold')
    try:
        threshold_value = float(threshold) if threshold is not None else 0.6
    except ValueError:
        return Response(
            {'error': 'El parámetro satisfaction_threshold debe ser numérico.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if summary['satisfaction_rate'] < threshold_value:
        guardrail_passed = False
        messages.append(
            f"La satisfacción ({summary['satisfaction_rate']:.2%}) está por debajo del umbral {threshold_value:.2%}."
        )

    if not messages:
        messages.append('Todos los guardrails están en verde.')

    return Response(
        {
            'guardrail_passed': guardrail_passed,
            'messages': messages,
            'latest_experiment': ExperimentRunSerializer(latest_experiment).data if latest_experiment else None,
            'metrics': {
                'total_feedback': summary['total'],
                'satisfaction_rate': summary['satisfaction_rate'],
                'net_score': summary['net_score'],
                'failed_feedback_events': failed_events,
            },
            'generated_at': summary['generated_at'],
        }
    )


# ====================================
# VISTAS RAG (RETRIEVAL-AUGMENTED GENERATION)
# ====================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rag_status(request):
    """
    Obtener estado del sistema RAG
    """
    if not RAG_MODULES_AVAILABLE:
        return Response({
            'rag_available': False,
            'error': 'Sistema RAG no disponible. Instalar dependencias.'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        try:
            pipeline = RAGPipeline()
            readiness = pipeline.is_ready()
            rag_status_data = {
                "modules_available": RAG_MODULES_AVAILABLE,
                "components": readiness,
                "version": "1.0.0"
            }
        except Exception as e:
            logger.error(f"Error obteniendo estado RAG: {e}")
            rag_status_data = {
                "modules_available": False,
                "error": str(e)
            }
        
        return Response({
            'rag_available': True,
            'status': rag_status_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado RAG: {e}")
        return Response({
            'error': 'Error obteniendo estado del sistema RAG',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_initialize(request):
    """
    Inicializar sistema RAG
    """
    if not RAG_MODULES_AVAILABLE:
        return Response({
            'error': 'Sistema RAG no disponible'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        try:
            pipeline = RAGPipeline()
            readiness = pipeline.is_ready()
            result = {
                "success": True,
                "components": readiness,
                "message": "Sistema RAG inicializado"
            }
        except Exception as e:
            logger.error(f"Error inicializando RAG: {e}")
            result = {
                "success": False,
                "error": str(e)
            }
        
        if result['success']:
            return Response({
                'message': 'Sistema RAG inicializado correctamente',
                'result': result
            })
        else:
            return Response({
                'error': 'Error inicializando sistema RAG',
                'details': result.get('error', 'Unknown error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error inicializando RAG: {e}")
        return Response({
            'error': 'Error inicializando sistema RAG',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_sync_documents(request):
    """
    Sincronizar documentos desde Google Drive y procesarlos
    """
    if not RAG_MODULES_AVAILABLE:
        return Response({
            'error': 'Sistema RAG no disponible'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        force_reprocess = request.data.get('force_reprocess', False)
        
        pipeline = RAGPipeline()
        result = pipeline.sync_and_process_documents(force_reprocess=force_reprocess)
        
        if result['success']:
            return Response({
                'message': 'Documentos sincronizados y procesados correctamente',
                'result': result
            })
        else:
            return Response({
                'error': 'Error en sincronización de documentos',
                'details': result.get('error', 'Unknown error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error sincronizando documentos: {e}")
        return Response({
            'error': 'Error sincronizando documentos',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def rag_query(request):
    """
    Realizar consulta RAG con recuperación adaptativa de documentos
    """
    if not RAG_MODULES_AVAILABLE:
        return Response({
            'error': 'Sistema RAG no disponible'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    question = request.data.get('question', '').strip()
    
    if not question:
        return Response({
            'error': 'Pregunta requerida'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Sistema adaptativo: calcular top_k basado en complejidad de consulta
        if 'top_k' in request.data:
            top_k = request.data.get('top_k')
        else:
            # Calcular top_k dinámico
            top_k = calculate_adaptive_top_k(question)
        
        include_generation = request.data.get('include_generation', True)
        
        logger.info(f"📊 Consulta con top_k adaptativo: {top_k} (longitud: {len(question)} chars)")
        
        pipeline = RAGPipeline()
        result = pipeline.query(
            question=question,
            top_k=top_k,
            include_generation=include_generation
        )
        
        if result['success']:
            return Response({
                'question': question,
                'answer': result.get('answer'),
                'sources': result.get('sources', []),
                'relevant_documents_count': len(result.get('relevant_documents', [])),
                'generation_used': result.get('generation_used', False),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return Response({
                'error': 'Error procesando consulta RAG',
                'details': result.get('error', 'Unknown error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error en consulta RAG: {e}")
        return Response({
            'error': 'Error procesando consulta RAG',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rag_enhanced_chat(request):
    """
    Chat mejorado con RAG - Integra RAG en las conversaciones normales
    ✨ AHORA CON TRACKING DE MÉTRICAS PARA TESIS
    """
    if not RAG_MODULES_AVAILABLE:
        # Fallback al chat normal si RAG no está disponible
        return send_message(request)
    
    # ✨ INICIAR TRACKING DE MÉTRICAS
    from .metrics_tracker import MetricsTracker
    tracker = MetricsTracker()
    
    try:
        conversation_id = request.data.get('conversation_id')
        content = request.data.get('content', '').strip()
        use_rag = request.data.get('use_rag', True)
        
        if not content:
            return Response({
                'error': 'Contenido del mensaje requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Detectar si es un saludo simple (solo desactivar RAG para saludos básicos)
        normalized_content = content.lower()
        greeting_keywords = ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'hello', 'hi', 'hey']
        
        # Solo desactivar RAG si es un saludo simple y muy corto
        is_simple_greeting = (
            any(normalized_content.startswith(word) for word in greeting_keywords) 
            and len(content) <= 30  # Saludos muy cortos
        )

        if use_rag and is_simple_greeting:
            use_rag = False
        
        # Obtener o crear conversación
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            except Conversation.DoesNotExist:
                return Response({
                    'error': 'Conversación no encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            conversation = Conversation.objects.create(
                user=request.user,
                title=content[:50] + '...' if len(content) > 50 else content
            )
        
        # Guardar mensaje del usuario
        user_message = Message.objects.create(
            conversation=conversation,
            text=content,
            sender='user'
        )
        
        # ✨ INICIAR TRACKING DE LA CONSULTA
        tracker.start_query(content, user=request.user, conversation=conversation)
        
        # Variable para almacenar las fuentes
        sources = []
        
        # Generar respuesta
        if use_rag:
            # ✨ INICIAR MEDICIÓN DE RECUPERACIÓN
            tracker.start_retrieval()
            
            # Calcular top_k dinámico basado en complejidad
            adaptive_top_k = calculate_adaptive_top_k(content)
            logger.info(f"📊 RAG Chat - top_k adaptativo: {adaptive_top_k}")
            
            # Usar RAG para generar respuesta
            pipeline = RAGPipeline()
            rag_result = pipeline.query(
                question=content,
                top_k=adaptive_top_k,
                include_generation=True
            )
            
            # ✨ FINALIZAR MEDICIÓN DE RECUPERACIÓN
            sources_count = len(rag_result.get('sources', []))
            tracker.end_retrieval(num_documents=sources_count, k=adaptive_top_k)
            
            # ✨ INICIAR MEDICIÓN DE GENERACIÓN
            tracker.start_generation()
            
            if rag_result['success'] and rag_result.get('answer'):
                response_content = rag_result['answer']
                sources = rag_result.get('sources', [])
                
                # ✨ MARCAR PRIMER TOKEN (asumimos que ya se generó)
                tracker.mark_first_token()
                
                # ✨ CAPTURAR RESPUESTA Y CONTEXTOS PARA RAGAS
                # Extraer el texto de los contextos recuperados
                contexts_text = [
                    source.get('content', '') or source.get('text', '')
                    for source in sources
                    if source.get('content') or source.get('text')
                ]
                tracker.set_answer_and_contexts(response_content, contexts_text)
                
                # NO agregar fuentes al texto del mensaje
                # Las fuentes se envían por separado en la respuesta JSON
            else:
                # Respuesta genérica si RAG falla
                response_content = "Lo siento, no pude encontrar información relevante en los documentos para responder tu pregunta. ¿Podrías ser más específico?"
                tracker.mark_first_token()
            
            # ✨ FINALIZAR MEDICIÓN DE GENERACIÓN
            tracker.end_generation()
        else:
            # Respuesta básica sin RAG
            tracker.mark_first_token()
            response_content = generate_basic_response(content)
        
        # Guardar respuesta del asistente
        assistant_message = Message.objects.create(
            conversation=conversation,
            text=response_content,
            sender='bot'
        )
        
        # Guardar las fuentes si están disponibles
        if sources:
            assistant_message.set_sources(sources)
            assistant_message.save()
        
        # Actualizar timestamp de conversación
        conversation.save()
        
        # ✨ GUARDAR MÉTRICAS EN BASE DE DATOS
        saved_metrics = tracker.save_metrics()
        if saved_metrics:
            logger.info(f"✅ Métricas guardadas para query: {saved_metrics.query_id[:8]}")
        
        return Response({
            'conversation_id': conversation.id,
            'user_message': {
                'id': user_message.id,
                'content': user_message.text,
                'timestamp': user_message.created_at.isoformat()
            },
            'assistant_message': {
                'id': assistant_message.id,
                'content': assistant_message.text,
                'timestamp': assistant_message.created_at.isoformat(),
                'rating': None,
                'rating_issue_tag': Rating.IssueTag.NONE,
            },
            'response': response_content,  # Para compatibilidad con el frontend
            'rag_used': use_rag and RAG_MODULES_AVAILABLE,
            'sources': sources,
            'metrics': tracker.get_summary()  # ✨ INCLUIR MÉTRICAS EN RESPUESTA
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"❌ Error en chat RAG: {e}")
        # Intentar guardar métricas incluso si hay error
        try:
            tracker.save_metrics()
        except:
            pass
        
        return Response({
            'error': 'Error procesando mensaje con RAG',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def rag_system_status(request):
    """
    Estado detallado del sistema RAG para administradores
    """
    if not RAG_MODULES_AVAILABLE:
        return Response({
            'rag_available': False,
            'error': 'Sistema RAG no disponible'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    try:
        pipeline = RAGPipeline()
        system_status = pipeline.get_system_status()
        
        return Response({
            'rag_available': True,
            'system_status': system_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado completo RAG: {e}")
        return Response({
            'error': 'Error obteniendo estado del sistema',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================================
# AUTENTICACIÓN - REGISTRO
# ================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Registrar un nuevo usuario con validaciones estrictas
    """
    try:
        username = request.data.get('username', '').strip()
        email = request.data.get('email', '').strip()
        password = request.data.get('password', '').strip()
        
        # Validación de username vacío
        if not username:
            logger.warning(f"❌ Registro fallido: username vacío")
            return Response(
                {'error': 'El nombre de usuario es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar longitud de username (3-20 caracteres)
        if len(username) < 3:
            logger.warning(f"❌ Registro fallido: username muy corto ({username})")
            return Response(
                {'error': 'El nombre de usuario debe tener al menos 3 caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(username) > 20:
            logger.warning(f"❌ Registro fallido: username muy largo ({username})")
            return Response(
                {'error': 'El nombre de usuario no puede tener más de 20 caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar caracteres en username (solo letras, números y guion bajo)
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            logger.warning(f"❌ Registro fallido: username con caracteres inválidos ({username})")
            return Response(
                {'error': 'El nombre de usuario solo puede contener letras, números y guion bajo (_)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que empiece con letra
        if not username[0].isalpha():
            logger.warning(f"❌ Registro fallido: username no empieza con letra ({username})")
            return Response(
                {'error': 'El nombre de usuario debe comenzar con una letra'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validación de email vacío
        if not email:
            logger.warning(f"❌ Registro fallido: email vacío (username: {username})")
            return Response(
                {'error': 'El email es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar formato de email
        # Regex mejorado: no permite puntos consecutivos, ni al inicio/final del local part
        email_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            logger.warning(f"❌ Registro fallido: formato email inválido ({email})")
            return Response(
                {'error': 'El formato del email no es válido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que no tenga puntos consecutivos
        if '..' in email:
            logger.warning(f"❌ Registro fallido: email con puntos consecutivos ({email})")
            return Response(
                {'error': 'El email no puede contener puntos consecutivos (..)'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validación de contraseña vacía
        if not password:
            logger.warning(f"❌ Registro fallido: contraseña vacía (username: {username})")
            return Response(
                {'error': 'La contraseña es requerida'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Validar longitud mínima de contraseña
        if len(password) < 6:
            logger.warning(f"❌ Registro fallido: contraseña muy corta (username: {username})")
            return Response(
                {'error': 'La contraseña debe tener al menos 6 caracteres'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que contenga al menos una letra y un número
        if not re.search(r'[a-zA-Z]', password) or not re.search(r'[0-9]', password):
            logger.warning(f"❌ Registro fallido: contraseña sin letra/número (username: {username})")
            return Response(
                {'error': 'La contraseña debe contener al menos una letra y un número'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            logger.warning(f"❌ Registro fallido: username ya existe ({username})")
            return Response(
                {'error': 'El nombre de usuario ya está en uso'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if User.objects.filter(email=email).exists():
            logger.warning(f"❌ Registro fallido: email ya registrado ({email})")
            return Response(
                {'error': 'El email ya está registrado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear el usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        logger.info(f"✅ Usuario registrado: {username}")
        
        return Response({
            'message': 'Usuario registrado exitosamente',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error registrando usuario: {str(e)}")
        return Response(
            {'error': 'Error interno del servidor'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )