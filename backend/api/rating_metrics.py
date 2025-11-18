"""
Rating Metrics - Métricas de calificaciones para panel admin
=============================================================

Endpoint que procesa y devuelve estadísticas de calificaciones de usuarios
"""

import logging
from datetime import datetime, timedelta
from django.db.models import Count, Q, Avg
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Rating, Message
from .admin_views import admin_required

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@admin_required
def get_rating_metrics(request):
    """
    Obtener métricas y estadísticas de calificaciones
    
    Returns:
        - Total de calificaciones
        - Distribución like/dislike
        - Calificaciones por período (última semana, mes)
        - Tags de problemas más comunes
        - Mensajes más votados (positivos y negativos)
    """
    try:
        # Total de calificaciones
        total_ratings = Rating.objects.count()
        
        if total_ratings == 0:
            return Response({
                "success": True,
                "total_ratings": 0,
                "message": "No hay calificaciones aún"
            })
        
        # Distribución de calificaciones
        distribution = Rating.objects.values('value').annotate(count=Count('id'))
        likes = sum(item['count'] for item in distribution if item['value'] == 'like')
        dislikes = sum(item['count'] for item in distribution if item['value'] == 'dislike')
        
        # Porcentajes
        like_percentage = round((likes / total_ratings) * 100, 1) if total_ratings > 0 else 0
        dislike_percentage = round((dislikes / total_ratings) * 100, 1) if total_ratings > 0 else 0
        
        # Calificaciones por período
        now = timezone.now()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)
        
        ratings_last_week = Rating.objects.filter(created_at__gte=last_week).count()
        ratings_last_month = Rating.objects.filter(created_at__gte=last_month).count()
        
        # Tags de problemas más comunes (solo en dislikes)
        issue_tags = Rating.objects.filter(
            value='dislike'
        ).exclude(
            issue_tag='none'
        ).values('issue_tag').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Convertir a formato legible
        issue_tags_formatted = []
        for tag in issue_tags:
            issue_tags_formatted.append({
                'tag': tag['issue_tag'],
                'label': dict(Rating.IssueTag.choices).get(tag['issue_tag'], tag['issue_tag']),
                'count': tag['count']
            })
        
        # Mensajes más votados (positivos)
        top_liked_messages = Rating.objects.filter(
            value='like'
        ).values(
            'message__text',
            'message__id'
        ).annotate(
            likes=Count('id')
        ).order_by('-likes')[:5]
        
        top_liked = []
        for item in top_liked_messages:
            text = item['message__text']
            top_liked.append({
                'message_id': item['message__id'],
                'text': text[:200] + '...' if len(text) > 200 else text,
                'likes': item['likes']
            })
        
        # Mensajes más votados (negativos)
        top_disliked_messages = Rating.objects.filter(
            value='dislike'
        ).values(
            'message__text',
            'message__id'
        ).annotate(
            dislikes=Count('id')
        ).order_by('-dislikes')[:5]
        
        top_disliked = []
        for item in top_disliked_messages:
            text = item['message__text']
            top_disliked.append({
                'message_id': item['message__id'],
                'text': text[:200] + '...' if len(text) > 200 else text,
                'dislikes': item['dislikes']
            })
        
        # Calificaciones recientes (últimas 10)
        recent_ratings = Rating.objects.select_related(
            'user', 'message'
        ).order_by('-created_at')[:10]
        
        recent_list = []
        for rating in recent_ratings:
            recent_list.append({
                'id': rating.id,
                'value': rating.value,
                'username': rating.user.username,
                'message_preview': rating.message.text[:100] + '...' if len(rating.message.text) > 100 else rating.message.text,
                'comment': rating.comment or '',
                'issue_tag': rating.issue_tag,
                'issue_tag_label': dict(Rating.IssueTag.choices).get(rating.issue_tag, rating.issue_tag),
                'created_at': rating.created_at.isoformat()
            })
        
        return Response({
            "success": True,
            "total_ratings": total_ratings,
            "distribution": {
                "likes": likes,
                "dislikes": dislikes,
                "like_percentage": like_percentage,
                "dislike_percentage": dislike_percentage
            },
            "period_stats": {
                "last_week": ratings_last_week,
                "last_month": ratings_last_month
            },
            "top_issues": issue_tags_formatted,
            "top_liked_messages": top_liked,
            "top_disliked_messages": top_disliked,
            "recent_ratings": recent_list
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas de calificaciones: {e}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
