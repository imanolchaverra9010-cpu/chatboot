# Características Avanzadas del Chatbot

## 🚀 Extensiones y Mejoras

### 1. Sistema de Comandos

Agrega comandos especiales que los usuarios pueden invocar:

```python
# En views.py, dentro de process_message()

def handle_commands(message_text, conversation):
    """Manejar comandos especiales"""
    
    if not message_text.startswith('/'):
        return None
    
    command = message_text.lower().split()[0]
    
    commands = {
        '/ayuda': 'Comandos disponibles:\n/ayuda - Muestra esta ayuda\n/info - Información del bot\n/historial - Tu historial de mensajes\n/reset - Reiniciar conversación',
        '/info': 'Soy un chatbot inteligente powered by Google Gemini 🤖\nEstoy aquí para ayudarte 24/7',
        '/historial': f'Has enviado {conversation.messages.count()} mensajes',
        '/reset': 'Conversación reiniciada. ¡Comencemos de nuevo!'
    }
    
    response = commands.get(command, 'Comando no reconocido. Usa /ayuda')
    
    if command == '/reset':
        # Limpiar contexto
        BotContext.objects.filter(conversation=conversation).delete()
    
    return response

# En process_message, antes de llamar a Gemini:
if message_type == 'text':
    # Verificar si es un comando
    command_response = handle_commands(content, conversation)
    if command_response:
        whatsapp_service.send_text_message(from_number, command_response)
        return  # No procesar con Gemini
    
    # Continuar con flujo normal de Gemini...
```

### 2. Detección de Intención

Clasifica automáticamente la intención del usuario:

```python
# Crear nuevo archivo: chatbot/services/intent_service.py

class IntentService:
    """Detecta la intención del mensaje del usuario"""
    
    INTENTS = {
        'saludo': ['hola', 'buenos días', 'buenas tardes', 'hey', 'qué tal'],
        'despedida': ['adiós', 'chao', 'hasta luego', 'nos vemos'],
        'ayuda': ['ayuda', 'ayúdame', 'no entiendo', 'cómo'],
        'info': ['información', 'cuéntame', 'qué es', 'explica'],
        'queja': ['problema', 'error', 'no funciona', 'malo', 'queja'],
        'agradecimiento': ['gracias', 'thank you', 'excelente', 'perfecto']
    }
    
    @classmethod
    def detect_intent(cls, message):
        """Detectar intención del mensaje"""
        message_lower = message.lower()
        
        for intent, keywords in cls.INTENTS.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        return 'general'
    
    @classmethod
    def get_quick_response(cls, intent):
        """Respuestas rápidas según intención"""
        quick_responses = {
            'saludo': '¡Hola! 👋 ¿En qué puedo ayudarte hoy?',
            'despedida': '¡Hasta luego! 👋 Que tengas un excelente día',
            'agradecimiento': '¡De nada! 😊 Estoy aquí para ayudarte',
        }
        return quick_responses.get(intent)

# En views.py
from chatbot.services.intent_service import IntentService

def process_message(message_data, value):
    # ... código existente ...
    
    if message_type == 'text':
        # Detectar intención
        intent = IntentService.detect_intent(content)
        
        # Respuesta rápida para intenciones simples
        quick_response = IntentService.get_quick_response(intent)
        if quick_response:
            whatsapp_service.send_text_message(from_number, quick_response)
            # Guardar en BotContext para tracking
            context_obj, _ = BotContext.objects.get_or_create(conversation=conversation)
            context_obj.last_intent = intent
            context_obj.save()
            return
        
        # Continuar con Gemini para intenciones complejas...
```

### 3. Respuestas con Botones (Interactive Messages)

```python
# En whatsapp_service.py

def send_interactive_buttons(self, to_number, text, buttons):
    """
    Enviar mensaje con botones interactivos
    
    Args:
        to_number: Número del destinatario
        text: Texto del mensaje
        buttons: Lista de dicts [{'id': 'btn1', 'title': 'Opción 1'}, ...]
    """
    url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
    
    # Máximo 3 botones
    buttons_formatted = [
        {
            "type": "reply",
            "reply": {
                "id": btn['id'],
                "title": btn['title'][:20]  # Máx 20 caracteres
            }
        }
        for btn in buttons[:3]
    ]
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": text
            },
            "action": {
                "buttons": buttons_formatted
            }
        }
    }
    
    try:
        response = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json().get('messages', [{}])[0].get('id')
    except Exception as e:
        logger.error(f"Error enviando botones: {str(e)}")
        return None

# Uso en views.py
def send_welcome_buttons(from_number):
    whatsapp = WhatsAppService()
    whatsapp.send_interactive_buttons(
        from_number,
        "¡Hola! ¿En qué puedo ayudarte?",
        [
            {'id': 'help', 'title': '🆘 Ayuda'},
            {'id': 'info', 'title': 'ℹ️ Información'},
            {'id': 'contact', 'title': '📞 Contacto'}
        ]
    )
```

### 4. Listas Interactivas

```python
# En whatsapp_service.py

def send_interactive_list(self, to_number, text, button_text, sections):
    """
    Enviar lista interactiva
    
    Args:
        to_number: Número del destinatario
        text: Texto del mensaje
        button_text: Texto del botón (ej: "Ver opciones")
        sections: Lista de secciones con opciones
            [
                {
                    'title': 'Sección 1',
                    'rows': [
                        {'id': 'opt1', 'title': 'Opción 1', 'description': 'Desc'},
                        ...
                    ]
                }
            ]
    """
    url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {
                "text": text
            },
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
    }
    
    try:
        response = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json().get('messages', [{}])[0].get('id')
    except Exception as e:
        logger.error(f"Error enviando lista: {str(e)}")
        return None

# Uso
whatsapp.send_interactive_list(
    phone_number,
    "Selecciona una categoría:",
    "Ver opciones",
    [
        {
            'title': 'Productos',
            'rows': [
                {'id': 'prod1', 'title': 'Laptops', 'description': 'Ver laptops disponibles'},
                {'id': 'prod2', 'title': 'Teléfonos', 'description': 'Ver teléfonos'},
            ]
        },
        {
            'title': 'Servicios',
            'rows': [
                {'id': 'serv1', 'title': 'Soporte', 'description': 'Obtener soporte técnico'},
            ]
        }
    ]
)
```

### 5. Procesamiento de Imágenes

Analizar imágenes enviadas por usuarios:

```python
# En views.py

def process_image_message(message_data, conversation, from_number):
    """Procesar imágenes con Gemini Vision"""
    
    image_data = message_data.get('image', {})
    media_id = image_data.get('id')
    caption = image_data.get('caption', '')
    
    # Descargar imagen
    whatsapp = WhatsAppService()
    media_url = whatsapp.get_media_url(media_id)
    
    if not media_url:
        return "No pude procesar la imagen"
    
    # Analizar con Gemini Vision (Pro Vision)
    import google.generativeai as genai
    
    vision_model = genai.GenerativeModel('gemini-pro-vision')
    
    # Descargar imagen
    import requests
    image_response = requests.get(media_url, headers={'Authorization': f'Bearer {settings.META_ACCESS_TOKEN}'})
    
    if image_response.status_code == 200:
        # Analizar imagen
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(image_response.content))
        
        prompt = f"Describe esta imagen en detalle en español. {caption if caption else ''}"
        
        response = vision_model.generate_content([prompt, img])
        return response.text
    
    return "No pude analizar la imagen"

# En process_message:
elif message_type == 'image':
    response_text = process_image_message(message_data, conversation, from_number)
    whatsapp_service.send_text_message(from_number, response_text)
```

### 6. Recordatorios Programados

```python
# Crear: chatbot/management/commands/send_reminders.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chatbot.models import Conversation, BotContext
from chatbot.services.whatsapp_service import WhatsAppService

class Command(BaseCommand):
    help = 'Enviar recordatorios programados'
    
    def handle(self, *args, **options):
        # Buscar conversaciones inactivas por 24h
        yesterday = timezone.now() - timedelta(days=1)
        
        inactive_convs = Conversation.objects.filter(
            updated_at__lte=yesterday,
            is_active=True
        )
        
        whatsapp = WhatsAppService()
        
        for conv in inactive_convs:
            message = "¡Hola! 👋 ¿Hay algo más en lo que pueda ayudarte?"
            whatsapp.send_text_message(conv.phone_number, message)
            self.stdout.write(f"Recordatorio enviado a {conv.phone_number}")

# Configurar cron job (Linux):
# crontab -e
# 0 10 * * * cd /path/to/project && venv/bin/python manage.py send_reminders
```

### 7. Métricas y Analytics

```python
# Crear: chatbot/models.py (agregar al final)

class Analytics(models.Model):
    """Métricas del chatbot"""
    date = models.DateField(auto_now_add=True)
    total_messages = models.IntegerField(default=0)
    total_conversations = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)
    top_intent = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = 'Analytics'
        verbose_name_plural = 'Analytics'
        ordering = ['-date']

# Crear: chatbot/management/commands/generate_analytics.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from chatbot.models import Message, Conversation, Analytics, BotContext

class Command(BaseCommand):
    help = 'Generar métricas diarias'
    
    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Contar mensajes del día
        messages_today = Message.objects.filter(
            created_at__date=today
        ).count()
        
        # Conversaciones activas
        conversations_today = Conversation.objects.filter(
            updated_at__date=today
        ).count()
        
        # Intención más común
        top_intent = BotContext.objects.filter(
            updated_at__date=today
        ).values('last_intent').annotate(
            count=Count('last_intent')
        ).order_by('-count').first()
        
        # Guardar analytics
        Analytics.objects.create(
            date=today,
            total_messages=messages_today,
            total_conversations=conversations_today,
            top_intent=top_intent['last_intent'] if top_intent else 'N/A'
        )
        
        self.stdout.write(self.style.SUCCESS(f'Analytics generados para {today}'))

# Ejecutar diariamente con cron
```

### 8. Integración con Base de Datos de Productos

```python
# Crear: chatbot/models.py (agregar)

class Product(models.Model):
    """Catálogo de productos"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    category = models.CharField(max_length=100)
    image_url = models.URLField(blank=True)
    
    def __str__(self):
        return self.name

# Crear: chatbot/services/product_service.py

from chatbot.models import Product
from difflib import get_close_matches

class ProductService:
    """Búsqueda de productos"""
    
    @staticmethod
    def search_products(query):
        """Buscar productos por nombre o descripción"""
        products = Product.objects.filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query)
        )[:5]
        
        return products
    
    @staticmethod
    def format_product_info(products):
        """Formatear información de productos"""
        if not products:
            return "No encontré productos que coincidan con tu búsqueda."
        
        result = "📦 *Productos encontrados:*\n\n"
        
        for product in products:
            result += f"*{product.name}*\n"
            result += f"💰 Precio: ${product.price}\n"
            result += f"📝 {product.description[:100]}...\n"
            result += f"{'✅ Disponible' if product.stock > 0 else '❌ Agotado'}\n\n"
        
        return result

# En views.py
from chatbot.services.product_service import ProductService

def process_message(message_data, value):
    # ... código existente ...
    
    if message_type == 'text':
        # Detectar si busca productos
        if any(word in content.lower() for word in ['producto', 'buscar', 'precio', 'comprar']):
            products = ProductService.search_products(content)
            if products:
                response_text = ProductService.format_product_info(products)
                whatsapp_service.send_text_message(from_number, response_text)
                
                # Enviar imágenes de productos
                for product in products[:3]:
                    if product.image_url:
                        whatsapp_service.send_image(
                            from_number,
                            product.image_url,
                            f"{product.name} - ${product.price}"
                        )
                return
```

### 9. Webhooks de Estado de Mensajes

```python
# En views.py, modificar handle_webhook:

def handle_webhook(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
        
        for entry in body.get('entry', []):
            for change in entry.get('changes', []):
                field = change.get('field')
                value = change.get('value', {})
                
                # Manejar mensajes
                if field == 'messages':
                    messages = value.get('messages', [])
                    for message_data in messages:
                        process_message(message_data, value)
                
                # Manejar estados (entregado, leído, etc.)
                elif field == 'message_status':
                    statuses = value.get('statuses', [])
                    for status_data in statuses:
                        update_message_status(status_data)
        
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error'}, status=500)

def update_message_status(status_data):
    """Actualizar estado de mensaje"""
    message_id = status_data.get('id')
    status = status_data.get('status')  # sent, delivered, read
    
    try:
        message = Message.objects.get(message_id=message_id)
        message.status = status
        message.save()
        logger.info(f"Mensaje {message_id} actualizado a {status}")
    except Message.DoesNotExist:
        pass
```

### 10. Rate Limiting

```python
# Crear: chatbot/middleware.py

from django.core.cache import cache
from django.http import JsonResponse
import time

class RateLimitMiddleware:
    """Limitar solicitudes por número de teléfono"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/chatbot/webhook/') and request.method == 'POST':
            # Extraer número de teléfono del body
            try:
                import json
                body = json.loads(request.body.decode('utf-8'))
                phone = self.extract_phone(body)
                
                if phone:
                    # Verificar rate limit (5 mensajes por minuto)
                    cache_key = f'rate_limit_{phone}'
                    requests = cache.get(cache_key, [])
                    now = time.time()
                    
                    # Filtrar requests de último minuto
                    requests = [r for r in requests if now - r < 60]
                    
                    if len(requests) >= 5:
                        return JsonResponse({
                            'error': 'Rate limit exceeded'
                        }, status=429)
                    
                    requests.append(now)
                    cache.set(cache_key, requests, 60)
            except:
                pass
        
        return self.get_response(request)
    
    def extract_phone(self, body):
        """Extraer número de teléfono del webhook"""
        try:
            return body['entry'][0]['changes'][0]['value']['messages'][0]['from']
        except:
            return None

# En settings.py
MIDDLEWARE = [
    # ... otros middleware ...
    'chatbot.middleware.RateLimitMiddleware',
]
```

## 🎯 Ejemplo Completo: Bot de Restaurante

```python
# Implementación completa combinando características

# En views.py
def process_restaurant_message(message, conversation, from_number):
    """Bot especializado para restaurante"""
    
    whatsapp = WhatsAppService()
    
    # Menú
    if 'menu' in message.lower() or 'carta' in message.lower():
        whatsapp.send_interactive_list(
            from_number,
            "🍽️ Nuestro Menú",
            "Ver opciones",
            [
                {
                    'title': 'Entradas',
                    'rows': [
                        {'id': 'ent1', 'title': 'Ensalada César', 'description': '$12'},
                        {'id': 'ent2', 'title': 'Sopa del día', 'description': '$8'},
                    ]
                },
                {
                    'title': 'Platos Principales',
                    'rows': [
                        {'id': 'main1', 'title': 'Pasta Carbonara', 'description': '$18'},
                        {'id': 'main2', 'title': 'Filete', 'description': '$25'},
                    ]
                }
            ]
        )
        return True
    
    # Reservas
    if 'reserva' in message.lower() or 'mesa' in message.lower():
        whatsapp.send_interactive_buttons(
            from_number,
            "¿Para cuántas personas?",
            [
                {'id': 'res_2', 'title': '2 personas'},
                {'id': 'res_4', 'title': '4 personas'},
                {'id': 'res_6', 'title': '6+ personas'}
            ]
        )
        return True
    
    return False
```

---

**Estas características te permiten crear un chatbot profesional y completo para cualquier tipo de negocio.**
