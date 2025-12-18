"""
Views para manejar webhook de WhatsApp - VERSION CON DEBUG MEJORADO
"""
import logging
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import Conversation, Message
from .services.whatsapp_service import WhatsAppService
from .services.gemini_service import GeminiService

logger = logging.getLogger('chatbot')


@require_http_methods(["GET"])
def index(request):
    """
    View simple para confirmar que la URL base /chatbot/ está activa.
    """
    return HttpResponse(
        "<h1>WhatsApp Chatbot Online</h1>"
        "<p>Webhook: <a href='/chatbot/webhook/'>/chatbot/webhook/</a></p>"
        "<p>Status: <a href='/chatbot/status/'>/chatbot/status/</a></p>",
        status=200
    )


@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook(request):
    """
    Endpoint del webhook de WhatsApp
    - GET: Verificación del webhook por parte de Meta
    - POST: Recepción de mensajes
    """
    
    # LOG CRÍTICO: Registrar TODA petición que llegue
    logger.info("="*80)
    logger.info(f"🔔 WEBHOOK LLAMADO - Método: {request.method}")
    logger.info(f"📍 Path: {request.path}")
    logger.info(f"🌐 Headers: {dict(request.headers)}")
    logger.info("="*80)
    
    if request.method == 'GET':
        return verify_webhook(request)
    elif request.method == 'POST':
        return handle_webhook(request)


def verify_webhook(request):
    """
    Verifica el webhook de Meta
    """
    # Obtener parámetros
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    
    # Log de debugging
    logger.info("="*60)
    logger.info("VERIFICACIÓN DE WEBHOOK")
    logger.info("="*60)
    logger.info(f"Parámetros recibidos:")
    logger.info(f"  - hub.mode: {mode}")
    logger.info(f"  - hub.verify_token: {token}")
    logger.info(f"  - hub.challenge: {challenge}")
    logger.info(f"Token esperado en settings: {settings.META_VERIFY_TOKEN}")
    logger.info(f"Tokens coinciden: {token == settings.META_VERIFY_TOKEN}")
    logger.info("="*60)
    
    # Validar parámetros
    if not mode:
        logger.error("❌ Falta parámetro hub.mode")
        return HttpResponse(
            'Error: Falta parámetro hub.mode\n\n'
            'URL correcta debe ser:\n'
            f'{request.build_absolute_uri()}?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=CHALLENGE',
            status=400
        )
    
    if not token:
        logger.error("❌ Falta parámetro hub.verify_token")
        return HttpResponse('Error: Falta parámetro hub.verify_token', status=400)
    
    if not challenge:
        logger.error("❌ Falta parámetro hub.challenge")
        return HttpResponse('Error: Falta parámetro hub.challenge', status=400)
    
    # Verificar modo
    if mode != 'subscribe':
        logger.error(f"❌ Modo incorrecto: {mode} (esperado: 'subscribe')")
        return HttpResponse(f'Error: Modo debe ser "subscribe", recibido: "{mode}"', status=400)
    
    # Verificar token
    if token != settings.META_VERIFY_TOKEN:
        logger.error("❌ Token de verificación incorrecto")
        logger.error(f"   Recibido: {token}")
        logger.error(f"   Esperado: {settings.META_VERIFY_TOKEN}")
        return HttpResponse('Error: Token de verificación incorrecto', status=403)
    
    # ✅ Verificación exitosa
    logger.info("✅ Webhook verificado exitosamente!")
    logger.info(f"   Devolviendo challenge: {challenge}")
    return HttpResponse(challenge, content_type='text/plain', status=200)


def handle_webhook(request):
    """
    Maneja los mensajes entrantes de WhatsApp
    """
    try:
        # LOG CRÍTICO: Registrar el body RAW
        raw_body = request.body.decode('utf-8')
        logger.info("="*80)
        logger.info("📨 POST RECIBIDO EN WEBHOOK")
        logger.info("="*80)
        logger.info(f"📦 Body RAW (primeros 500 chars):\n{raw_body[:500]}")
        logger.info("="*80)
        
        # Parsear body
        body = json.loads(raw_body)
        
        logger.info("="*60)
        logger.info("MENSAJE RECIBIDO - ESTRUCTURA COMPLETA")
        logger.info("="*60)
        logger.info(f"Body completo:\n{json.dumps(body, indent=2)}")
        logger.info("="*60)
        
        # Verificar que sea un mensaje de WhatsApp
        object_type = body.get('object')
        logger.info(f"🔍 Object type: {object_type}")
        
        if object_type != 'whatsapp_business_account':
            logger.warning(f"⚠️ Objeto ignorado: {object_type}")
            logger.warning(f"   Se esperaba: 'whatsapp_business_account'")
            return JsonResponse({'status': 'ignored', 'reason': f'object type is {object_type}'})
        
        # Procesar entradas
        entries = body.get('entry', [])
        logger.info(f"📋 Número de entries: {len(entries)}")
        
        if not entries:
            logger.warning("⚠️ No hay 'entry' en el body")
            return JsonResponse({'status': 'ignored', 'reason': 'no entries'})
        
        for entry_idx, entry in enumerate(entries):
            logger.info(f"🔄 Procesando entry {entry_idx + 1}/{len(entries)}")
            
            changes = entry.get('changes', [])
            logger.info(f"   📝 Número de changes: {len(changes)}")
            
            for change_idx, change in enumerate(changes):
                logger.info(f"   🔄 Procesando change {change_idx + 1}/{len(changes)}")
                
                field = change.get('field')
                logger.info(f"      🏷️ Field: {field}")
                
                if field != 'messages':
                    logger.info(f"      ⏭️ Campo ignorado: {field}")
                    continue
                
                value = change.get('value', {})
                logger.info(f"      📊 Value keys: {list(value.keys())}")
                
                # Verificar mensajes
                messages = value.get('messages', [])
                logger.info(f"      💬 Número de mensajes: {len(messages)}")
                
                if not messages:
                    logger.warning("      ⚠️ No hay mensajes en este change")
                    continue
                
                # Procesar cada mensaje
                for msg_idx, message_data in enumerate(messages):
                    logger.info(f"      🔄 Procesando mensaje {msg_idx + 1}/{len(messages)}")
                    logger.info(f"      📨 Message ID: {message_data.get('id')}")
                    logger.info(f"      📱 From: {message_data.get('from')}")
                    logger.info(f"      📖 Type: {message_data.get('type')}")
                    
                    process_message(message_data, value)
        
        logger.info("✅ Webhook procesado exitosamente")
        return JsonResponse({'status': 'ok'})
    
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error decodificando JSON: {str(e)}")
        logger.error(f"   Body recibido: {request.body.decode('utf-8')[:200]}")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"❌ Error procesando webhook: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def process_message(message_data, value):
    """
    Procesa un mensaje individual
    """
    try:
        # Extraer datos
        message_id = message_data.get('id')
        from_number = message_data.get('from')
        timestamp = message_data.get('timestamp')
        message_type = message_data.get('type')
        
        logger.info(f"      🔧 PROCESANDO MENSAJE")
        logger.info(f"         📱 De: {from_number}")
        logger.info(f"         📖 Tipo: {message_type}")
        logger.info(f"         🆔 ID: {message_id}")
        
        # Obtener/crear conversación
        contacts = value.get('contacts', [])
        contact_name = contacts[0].get('profile', {}).get('name', '') if contacts else ''
        
        logger.info(f"         👤 Nombre contacto: {contact_name}")
        
        conversation, created = Conversation.objects.get_or_create(
            phone_number=from_number,
            defaults={'name': contact_name}
        )
        
        if created:
            logger.info(f"         ✨ Nueva conversación creada: {from_number}")
        else:
            logger.info(f"         📂 Conversación existente: {conversation.id}")
        
        # Extraer contenido
        content = ""
        media_url = None
        
        if message_type == 'text':
            content = message_data.get('text', {}).get('body', '')
            logger.info(f"         💬 Contenido: {content}")
        elif message_type == 'image':
            image_data = message_data.get('image', {})
            content = image_data.get('caption', '[Imagen recibida]')
            media_url = image_data.get('id')
        elif message_type == 'audio':
            content = '[Audio recibido]'
            media_url = message_data.get('audio', {}).get('id')
        elif message_type == 'video':
            video_data = message_data.get('video', {})
            content = video_data.get('caption', '[Video recibido]')
            media_url = video_data.get('id')
        elif message_type == 'document':
            doc_data = message_data.get('document', {})
            content = f"[Documento: {doc_data.get('filename', 'sin nombre')}]"
            media_url = doc_data.get('id')
        elif message_type == 'location':
            loc_data = message_data.get('location', {})
            lat = loc_data.get('latitude')
            lon = loc_data.get('longitude')
            content = f"[Ubicación: {lat}, {lon}]" if lat and lon else "[Ubicación]"
        elif message_type == 'sticker':
            content = '[Sticker recibido]'
            media_url = message_data.get('sticker', {}).get('id')
        else:
            content = f"[{message_type.capitalize()} recibido]"

        # Guardar mensaje
        incoming_message = Message.objects.create(
            conversation=conversation,
            message_id=message_id,
            direction='incoming',
            message_type=message_type,
            content=content,
            media_url=media_url
        )
        
        logger.info(f"         💾 Mensaje guardado en BD: {incoming_message.id}")
        
        # Procesar respuesta
        if message_type == 'text':
            logger.info("         🤖 Generando respuesta con Gemini...")
            
            # Gemini
            gemini_service = GeminiService()
            recent_messages = conversation.get_recent_messages(limit=5)
            context = "\n".join([
                f"{'Usuario' if msg.direction == 'incoming' else 'Bot'}: {msg.content}"
                for msg in reversed(list(recent_messages))
            ])
            
            response_text = gemini_service.get_response(content, context)
            logger.info(f"         💡 Respuesta generada: {response_text[:100]}...")
            
            # Enviar por WhatsApp
            whatsapp_service = WhatsAppService()
            response_message_id = whatsapp_service.send_text_message(from_number, response_text)
            
            if response_message_id:
                Message.objects.create(
                    conversation=conversation,
                    message_id=response_message_id,
                    direction='outgoing',
                    message_type='text',
                    content=response_text,
                    status='sent'
                )
                logger.info(f"         ✅ Respuesta enviada: {response_message_id}")
            else:
                logger.error("         ❌ Error enviando respuesta")
        else:
            # Mensaje multimedia
            logger.info("         🖼️ Enviando respuesta para multimedia...")
            whatsapp_service = WhatsAppService()
            response_text = "He recibido tu mensaje multimedia. Por ahora solo respondo textos."
            whatsapp_service.send_text_message(from_number, response_text)
    
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje: {str(e)}", exc_info=True)


@require_http_methods(["GET"])
def status(request):
    """
    Endpoint para verificar el estado del bot
    """
    return JsonResponse({
        'status': 'online',
        'service': 'WhatsApp Chatbot',
        'version': '1.0.0',
        'configuration': {
            'verify_token_configured': bool(settings.META_VERIFY_TOKEN),
            'verify_token_value': settings.META_VERIFY_TOKEN,  # Para debugging
            'whatsapp_configured': bool(settings.META_PHONE_NUMBER_ID and settings.META_ACCESS_TOKEN),
            'phone_number_id': settings.META_PHONE_NUMBER_ID[:10] + '...' if settings.META_PHONE_NUMBER_ID else 'Not set',
            'access_token_length': len(settings.META_ACCESS_TOKEN) if settings.META_ACCESS_TOKEN else 0,
            'gemini_configured': bool(settings.GEMINI_API_KEY),
            'debug_mode': settings.DEBUG,
            'allowed_hosts': settings.ALLOWED_HOSTS,
        },
        'test_url': request.build_absolute_uri('/chatbot/webhook/') + '?hub.mode=subscribe&hub.verify_token=my_secure_verify_token&hub.challenge=TEST123'
    })