"""

Views para manejar webhook de WhatsApp - VERSION CON DEBUG MEJORADO

Incluye módulos: Informativo, Logístico, Analítico, Escalamiento

Procesa: texto, imágenes, audios, videos

"""

import logging

import json

import re

import os

import tempfile

from django.http import JsonResponse, HttpResponse

from django.shortcuts import render, redirect

from django.contrib import messages

from django.views.decorators.csrf import csrf_exempt

from django.views.decorators.http import require_http_methods, require_POST

from django.contrib.auth.decorators import login_required

from django.conf import settings

from .models import Conversation, Message

from .services.whatsapp_service import WhatsAppService

from .services.gemini_service import GeminiService

from .services.db_service import DatabaseService



logger = logging.getLogger('chatbot')





@require_http_methods(["GET"])

def index(request):

    """

    View simple para confirmar que la URL base /chatbot/ está activa.

    """

    return HttpResponse(

        "<h1>WhatsApp Chatbot Online</h1>"

        "<p><a href='/chatbot/inbox/'>📱 Inbox (mensajes)</a></p>"

        "<p><a href='/chatbot/webhook/'>Webhook</a> | "

        "<a href='/chatbot/status/'>Status</a></p>",

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

    logger.info(f"ðŸ“ Path: {request.path}")

    logger.info(f"ðŸŒ Headers: {dict(request.headers)}")

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

        logger.error("âŒ Falta parámetro hub.mode")

        return HttpResponse(

            'Error: Falta parámetro hub.mode\n\n'

            'URL correcta debe ser:\n'

            f'{request.build_absolute_uri()}?hub.mode=subscribe&hub.verify_token=TOKEN&hub.challenge=CHALLENGE',

            status=400

        )

    

    if not token:

        logger.error("âŒ Falta parámetro hub.verify_token")

        return HttpResponse('Error: Falta parámetro hub.verify_token', status=400)

    

    if not challenge:

        logger.error("âŒ Falta parámetro hub.challenge")

        return HttpResponse('Error: Falta parámetro hub.challenge', status=400)

    

    # Verificar modo

    if mode != 'subscribe':

        logger.error(f"âŒ Modo incorrecto: {mode} (esperado: 'subscribe')")

        return HttpResponse(f'Error: Modo debe ser "subscribe", recibido: "{mode}"', status=400)

    

    # Verificar token

    if token != settings.META_VERIFY_TOKEN:

        logger.error("âŒ Token de verificación incorrecto")

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

        logger.info(f"ðŸ” Object type: {object_type}")

        

        if object_type != 'whatsapp_business_account':

            logger.warning(f"âš ï¸ Objeto ignorado: {object_type}")

            logger.warning(f"   Se esperaba: 'whatsapp_business_account'")

            return JsonResponse({'status': 'ignored', 'reason': f'object type is {object_type}'})

        

        # Procesar entradas

        entries = body.get('entry', [])

        logger.info(f"📋 Número de entries: {len(entries)}")

        

        if not entries:

            logger.warning("âš ï¸ No hay 'entry' en el body")

            return JsonResponse({'status': 'ignored', 'reason': 'no entries'})

        

        for entry_idx, entry in enumerate(entries):

            logger.info(f"🔄 Procesando entry {entry_idx + 1}/{len(entries)}")

            

            changes = entry.get('changes', [])

            logger.info(f"   ðŸ“ Número de changes: {len(changes)}")

            

            for change_idx, change in enumerate(changes):

                logger.info(f"   🔄 Procesando change {change_idx + 1}/{len(changes)}")

                

                field = change.get('field')

                logger.info(f"      ðŸ·ï¸ Field: {field}")

                

                if field != 'messages':

                    logger.info(f"      â­ï¸ Campo ignorado: {field}")

                    continue

                

                value = change.get('value', {})

                logger.info(f"      ðŸ“Š Value keys: {list(value.keys())}")

                

                # Verificar mensajes

                messages = value.get('messages', [])

                logger.info(f"      💬 Número de mensajes: {len(messages)}")

                

                if not messages:

                    logger.warning("      âš ï¸ No hay mensajes en este change")

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

        logger.error(f"âŒ Error decodificando JSON: {str(e)}")

        logger.error(f"   Body recibido: {request.body.decode('utf-8')[:200]}")

        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    except Exception as e:

        logger.error(f"âŒ Error procesando webhook: {str(e)}", exc_info=True)

        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)





def _process_multimedia(message_type, message_data, conversation, from_number):

    """

    Descarga y procesa imagen, audio o video con Gemini.

    Retorna texto de respuesta.

    """

    media_id = None

    suffix = None

    caption = ""

    

    if message_type == 'image':

        image_data = message_data.get('image', {})

        media_id = image_data.get('id')

        caption = image_data.get('caption', '')

        suffix = '.jpg'

    elif message_type == 'sticker':

        sticker_data = message_data.get('sticker', {})

        media_id = sticker_data.get('id')

        suffix = '.webp'

    elif message_type == 'audio':

        audio_data = message_data.get('audio', {})

        media_id = audio_data.get('id')

        suffix = '.ogg'

    elif message_type == 'video':

        video_data = message_data.get('video', {})

        media_id = video_data.get('id')

        caption = video_data.get('caption', '')

        suffix = '.mp4'

    

    if not media_id:

        return "No pude obtener el archivo multimedia. Por favor intenta de nuevo."

    

    temp_path = None

    try:

        whatsapp_service = WhatsAppService()

        fd, temp_path = tempfile.mkstemp(suffix=suffix)

        os.close(fd)

        

        if not whatsapp_service.download_media(media_id, temp_path):

            return "No pude descargar el archivo. Verifica tu conexión e intenta de nuevo."

        

        gemini_service = GeminiService()

        recent_messages = conversation.get_recent_messages(limit=3)

        context = "\n".join([

            f"{'Usuario' if m.direction == 'incoming' else 'Bot'}: {m.content}"

            for m in reversed(list(recent_messages))

        ])

        

        if message_type in ('image', 'sticker'):

            logger.info("         ðŸ–¼ï¸ Analizando imagen/sticker con Gemini Vision...")

            response_text = gemini_service.analyze_image(temp_path, caption, context)

        elif message_type == 'audio':

            logger.info("         🎙️ Transcribiendo audio con Gemini...")

            transcript = gemini_service.transcribe_audio(temp_path)

            if transcript:

                logger.info("         🤖 Generando respuesta al audio...")

                full_context = "\n".join([

                    f"{'Usuario' if m.direction == 'incoming' else 'Bot'}: {m.content}"

                    for m in reversed(list(conversation.get_recent_messages(limit=5)))

                ])

                response_text = gemini_service.get_response(transcript, full_context, phone_number=from_number)

            else:

                response_text = "No pude transcribir el audio. Asegúrate de que sea claro y en español."

        elif message_type == 'video':

            logger.info("         🎞️ Procesando video con Gemini...")

            response_text = gemini_service.process_video(temp_path, caption, context)

        else:

            response_text = "He recibido tu mensaje. Por ahora proceso imágenes, audios y videos."

        

        return response_text

    

    except Exception as e:

        logger.error(f"Error procesando multimedia: {str(e)}", exc_info=True)

        return "Lo siento, hubo un error al procesar tu imagen/audio/video. Intenta de nuevo."

    

    finally:

        if temp_path and os.path.exists(temp_path):

            try:

                os.unlink(temp_path)

            except OSError:

                pass





def _extraer_documento(texto):

    """Extrae un documento numérico entre 6 y 12 dígitos."""

    if not texto:

        return None

    match = re.search(r"\b(\d{6,12})\b", texto)

    return match.group(1) if match else None





def _es_consulta_elecciones(texto):

    """Detecta mensajes relacionados con elecciones/puesto de votación."""

    if not texto:

        return False

    texto_limpio = texto.lower()

    keywords = [

        "eleccion", "elecciones", "votacion", "votación", "votar",

        "puesto", "mesa", "jurado", "documento", "cedula", "cédula",

    ]

    return any(kw in texto_limpio for kw in keywords)





def process_message(message_data, value):

    """

    Procesa un mensaje individual

    """

    try:

        # Extraer datos

        message_id = message_data.get('id')

        from_number = message_data.get('from')

        

        # Evitar duplicados: WhatsApp reintenta el webhook si no responde rápido

        if Message.objects.filter(message_id=message_id).exists():

            logger.info(f"         â­ï¸ Mensaje ya procesado (duplicado): {message_id}")

            return

        timestamp = message_data.get('timestamp')

        message_type = message_data.get('type')

        

        logger.info(f"      🛠️ PROCESANDO MENSAJE")

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

            whatsapp_service = WhatsAppService()

            response_text = None

            intent_detectado = 'general'

            db_service = DatabaseService()



            # === ELECCIONES ESTUDIANTILES: Consulta por documento ===

            documento = _extraer_documento(content)

            if documento:

                info_votacion = db_service.consultar_puesto_votacion(documento)

                if info_votacion:

                    response_text = (

                        "Informacion de votacion encontrada:\n"

                        f"Nombre: {info_votacion.get('nombre') or 'No registrado'}\n"

                        f"Documento: {info_votacion.get('documento')}\n"

                        f"Puesto: {info_votacion.get('puesto_votacion') or 'No registrado'}\n"

                        f"Mesa: {info_votacion.get('mesa') or 'No registrada'}\n"

                        f"Direccion: {info_votacion.get('direccion') or 'No registrada'}\n"

                        f"Zona: {info_votacion.get('zona') or 'No registrada'}"

                    )

                else:

                    response_text = (

                        "No encontré información de votación para ese documento.\n"

                        "Verifica el número e inténtalo de nuevo."

                    )

                intent_detectado = 'consulta_puesto_votacion'

            elif _es_consulta_elecciones(content):

                response_text = (

                    "Para consultarte el puesto de votación, envíame tu número de documento "

                    "(solo números, sin puntos)."

                )

                intent_detectado = 'solicitar_documento_votacion'



            # === ESCALAMIENTO: Usuario pide hablar con humano ===

            if response_text is None and (content.strip().upper() == 'HUMANO' or 'hablar con humano' in content.lower() or 'asesor' in content.lower()):

                escalamiento = db_service.crear_escalamiento(

                    conversation=conversation,

                    motivo=f"Usuario solicitó hablar con humano: {content}",

                    canal='whatsapp',

                    numero_whatsapp=from_number

                )

                db_service.registrar_consulta_analitica(

                    phone_number=from_number,

                    motivo_consulta=content,

                    intent_detectado='escalamiento_humano',

                    conversation=conversation,

                    escalado_humano=True,

                    metadata={'escalamiento_id': escalamiento.id if escalamiento else None}

                )

                numero_asesor = getattr(settings, 'ESCALAMIENTO_WHATSAPP', '') or ''

                if numero_asesor:

                    response_text = (

                        "¡Listo manito! ðŸ™‹â€â™‚ï¸ Un asesor te contactará pronto por este número.\n\n"

                        f"También puedes escribir directamente al: {numero_asesor}\n\n"

                        "Tu caso ha sido registrado para seguimiento."

                    )

                else:

                    response_text = (

                        "¡Entendido! ðŸ‘ Tu solicitud ha sido registrada.\n\n"

                        "Un asesor te contactará pronto. "

                        "Mientras tanto, dime en qué más puedo ayudarte."

                    )

                logger.info(f"         📤 Escalamiento creado para {from_number}")

            

            # === TURNOS: Reservar turno ===

            elif response_text is None and re.search(r'reservar\s*turno\s*(\d+)', content.lower()):

                match = re.search(r'reservar\s*turno\s*(\d+)', content.lower())

                if match:

                    turno_id = int(match.group(1))

                    turno = db_service.reservar_turno(turno_id, conversation, from_number)

                    if turno:

                        response_text = (

                            f"✅ ¡Listo manito! Turno reservado:\n"

                            f"🗓️ {turno.servicio}\n"

                            f"📅 {turno.fecha_turno}\n"

                            f"ðŸ• {turno.hora_inicio.strftime('%H:%M')}\n\n"

                            "Te esperamos. Si necesitas cancelar, escribe 'cancelar turno [número]'"

                        )

                        intent_detectado = 'reservar_turno'

                    else:

                        response_text = "Lo siento, ese turno ya no está disponible. Escribe 'turnos' para ver disponibilidad."

            

            # === TURNOS: Cancelar turno ===

            elif response_text is None and re.search(r'cancelar\s*turno\s*(\d+)', content.lower()):

                match = re.search(r'cancelar\s*turno\s*(\d+)', content.lower())

                if match:

                    turno_id = int(match.group(1))

                    ok = db_service.cancelar_turno(turno_id, from_number)

                    if ok:

                        response_text = "✅ Turno cancelado correctamente. Si necesitas otro, escribe 'turnos'."

                        intent_detectado = 'cancelar_turno'

                    else:

                        response_text = "No pude cancelar ese turno. Verifica que sea uno de tus turnos reservados."

            

            # === Respuesta con Gemini para el resto ===

            if response_text is None:

                logger.info("         🤖 Generando respuesta con Gemini...")

                gemini_service = GeminiService()

                recent_messages = conversation.get_recent_messages(limit=5)

                context = "\n".join([

                    f"{'Usuario' if msg.direction == 'incoming' else 'Bot'}: {msg.content}"

                    for msg in reversed(list(recent_messages))

                ])

                response_text = gemini_service.get_response(content, context, phone_number=from_number)

                logger.info(f"         💡 Respuesta generada: {response_text[:100]}...")

            

            # === MÓDULO ANALÍTICO: Registrar consulta ===

            try:

                db_service = DatabaseService()

                db_service.registrar_consulta_analitica(

                    phone_number=from_number,

                    motivo_consulta=content[:200],

                    intent_detectado=intent_detectado,

                    conversation=conversation,

                    resuelto=(response_text is not None),

                    metadata={}

                )

            except Exception as e:

                logger.warning(f"Error registrando consulta analítica: {e}")

            

            # Enviar por WhatsApp (asegurar texto válido)

            if not response_text or not str(response_text).strip():

                response_text = "Lo siento, no pude generar una respuesta. Escribe *HUMANO* para hablar con un asesor."

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

                logger.error("         âŒ Error enviando respuesta")

        else:

            # Procesar imagen, audio, video o sticker con Gemini

            if message_type in ('image', 'audio', 'video', 'sticker'):

                response_text = _process_multimedia(

                    message_type=message_type,

                    message_data=message_data,

                    conversation=conversation,

                    from_number=from_number,

                )

            elif message_type == 'location':

                # Procesar ubicación como texto

                content = incoming_message.content

                gemini_service = GeminiService()

                context = "\n".join([

                    f"{'Usuario' if m.direction == 'incoming' else 'Bot'}: {m.content}"

                    for m in reversed(list(conversation.get_recent_messages(limit=5)))

                ])

                response_text = gemini_service.get_response(

                    f"El usuario envió su ubicación: {content}. Ayúdame con información de lugares cercanos o cómo llegar.",

                    context, phone_number=from_number

                )

            else:

                response_text = "He recibido tu archivo. Por ahora proceso imágenes, audios, videos y stickers."

            

            if not response_text or not str(response_text).strip():

                response_text = "Lo siento, hubo un error. Escribe *HUMANO* para hablar con un asesor."

            whatsapp_service = WhatsAppService()

            whatsapp_service.send_text_message(from_number, response_text)

    

    except Exception as e:

        logger.error(f"âŒ Error procesando mensaje: {str(e)}", exc_info=True)





@login_required

def inbox(request):

    """Vista estilo WhatsApp: conversaciones y mensajes"""

    from django.db.models import Prefetch

    # No usar slice en Prefetch: Django filtra internamente y falla con "Cannot filter once slice taken"

    conversations = Conversation.objects.filter(is_active=True).prefetch_related(

        Prefetch('messages', queryset=Message.objects.order_by('-created_at'))

    ).order_by('-updated_at')[:50]

    

    for conv in conversations:

        last = conv.messages.first()  # primer mensaje del prefetch ordenado (el más reciente)

        conv.last_message = (last.content[:80] + '...') if last and len(last.content) > 80 else (last.content if last else None)

    

    return render(request, 'chatbot/inbox.html', {'conversations': conversations})





@login_required

def conversation_messages(request, conversation_id):

    """API: mensajes de una conversación en JSON"""

    try:

        conv = Conversation.objects.get(id=conversation_id)

        messages = conv.messages.order_by('created_at')[:200]

        data = {

            'messages': [

                {

                    'id': m.id,

                    'content': m.content,

                    'direction': m.direction,

                    'message_type': m.message_type,

                    'time': m.created_at.strftime('%H:%M'),

                    'date': m.created_at.strftime('%d/%m/%Y'),

                }

                for m in messages

            ]

        }

        return JsonResponse(data)

    except Conversation.DoesNotExist:

        return JsonResponse({'error': 'Conversación no encontrada'}, status=404)





@login_required

@require_POST

def send_alert(request):

    """Enviar alerta a usuario(s) por WhatsApp"""

    conversation_id = request.POST.get('conversation_id')

    scope = request.POST.get('scope', 'single')

    message = request.POST.get('message', '').strip()

    

    if not message:

        return redirect('chatbot:inbox')

    

    whatsapp = WhatsAppService()

    

    if scope == 'all':

        conversations = Conversation.objects.filter(is_active=True)

        sent = 0

        for conv in conversations:

            if conv.phone_number:

                if whatsapp.send_text_message(conv.phone_number, message):

                    sent += 1

        logger.info(f"Alerta enviada a {sent} conversaciones")

        messages.success(request, f'✅ Alerta enviada a {sent} conversaciones.')

    else:

        try:

            conv = Conversation.objects.get(id=conversation_id)

            if whatsapp.send_text_message(conv.phone_number, message):

                messages.success(request, '✅ Alerta enviada.')

        except Conversation.DoesNotExist:

            messages.error(request, 'Conversación no encontrada.')

    

    return redirect('chatbot:inbox')





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













