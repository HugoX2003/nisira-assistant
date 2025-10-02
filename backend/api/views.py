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

# RAG System imports
try:
    from rag_system import (
        get_rag_status,
        initialize_rag_system,
        sync_drive_documents,
        query_rag,
        RAG_MODULES_AVAILABLE
    )
    from rag_system.rag_engine.pipeline import RAGPipeline
except ImportError:
    RAG_MODULES_AVAILABLE = False
    RAGPipeline = None

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
            message_count = conv.messages.count()
            conversation_data.append({
                'id': conv.id,
                'title': conv.title,
                'created_at': conv.created_at.isoformat(),
                'updated_at': conv.updated_at.isoformat(),
                'message_count': message_count,
                'last_message': {
                    'content': last_message.text[:100] + '...' if last_message and len(last_message.text) > 100 else last_message.text if last_message else '',
                    'timestamp': last_message.created_at.isoformat() if last_message else None
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
        messages = conversation.messages.all().order_by('created_at')
        
        message_data = []
        for msg in messages:
            message_data.append({
                'id': msg.id,
                'content': msg.text,
                'is_user': msg.sender == 'user',
                'timestamp': msg.created_at.isoformat()
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
                'timestamp': user_message.created_at.isoformat()
            },
            'assistant_message': {
                'id': assistant_message.id,
                'content': assistant_message.text,
                'is_user': False,
                'timestamp': assistant_message.created_at.isoformat()
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
        rag_status_data = get_rag_status()
        
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
        result = initialize_rag_system()
        
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
    Realizar consulta RAG
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
        top_k = request.data.get('top_k', 5)
        include_generation = request.data.get('include_generation', True)
        
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
    """
    if not RAG_MODULES_AVAILABLE:
        # Fallback al chat normal si RAG no está disponible
        return send_message(request)
    
    try:
        conversation_id = request.data.get('conversation_id')
        content = request.data.get('content', '').strip()
        use_rag = request.data.get('use_rag', True)
        
        if not content:
            return Response({
                'error': 'Contenido del mensaje requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        # Variable para almacenar las fuentes
        sources = []
        
        # Generar respuesta
        if use_rag:
            # Usar RAG para generar respuesta
            pipeline = RAGPipeline()
            rag_result = pipeline.query(
                question=content,
                top_k=5,
                include_generation=True
            )
            
            if rag_result['success'] and rag_result.get('answer'):
                response_content = rag_result['answer']
                sources = rag_result.get('sources', [])
                
                # Agregar información de fuentes si están disponibles
                if sources:
                    source_text = "\n\n📚 Fuentes consultadas:\n"
                    for i, source in enumerate(sources[:3], 1):
                        source_text += f"{i}. {source.get('file_name', 'Documento')} (similitud: {source.get('similarity_score', 0):.2f})\n"
                    response_content += source_text
            else:
                # Respuesta genérica si RAG falla
                response_content = "Lo siento, no pude encontrar información relevante en los documentos para responder tu pregunta. ¿Podrías ser más específico?"
        else:
            # Respuesta básica sin RAG
            response_content = "Mensaje recibido. (Respuesta sin RAG - funcionalidad básica)"
        
        # Guardar respuesta del asistente
        assistant_message = Message.objects.create(
            conversation=conversation,
            text=response_content,
            sender='bot'
        )
        
        # Actualizar timestamp de conversación
        conversation.save()
        
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
                'timestamp': assistant_message.created_at.isoformat()
            },
            'rag_used': use_rag and RAG_MODULES_AVAILABLE,
            'sources': sources
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error en chat RAG: {e}")
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