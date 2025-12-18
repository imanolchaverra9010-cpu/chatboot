# WhatsApp Chatbot con Meta API, Django y Gemini

Un chatbot completo de WhatsApp que utiliza la API de Meta for Developers, Django como backend, y Google Gemini para respuestas inteligentes.

## 🚀 Características

- ✅ Integración completa con WhatsApp Business API
- ✅ Respuestas inteligentes usando Google Gemini
- ✅ Webhook para recibir mensajes en tiempo real
- ✅ Historial de conversaciones
- ✅ Panel de administración Django
- ✅ Manejo de mensajes de texto, imágenes y multimedia
- ✅ Sistema de verificación de webhook

## 📋 Requisitos Previos

1. **Cuenta de Meta for Developers**
   - Crear una app en https://developers.facebook.com/
   - Configurar WhatsApp Business API
   - Obtener Phone Number ID y Access Token

2. **Google Gemini API Key**
   - Obtener API key en https://makersuite.google.com/app/apikey

3. **Python 3.8+**

4. **Ngrok o servidor público** (para desarrollo local)

## 🔧 Instalación

### 1. Clonar y preparar el entorno

```bash
# Extraer el ZIP y navegar al directorio
cd whatsapp-chatbot-project

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Linux/Mac:
source venv/bin/activate
# En Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

**Variables requeridas:**

- `META_PHONE_NUMBER_ID`: ID del número de WhatsApp Business
- `META_ACCESS_TOKEN`: Token de acceso de Meta
- `META_VERIFY_TOKEN`: Token personalizado para verificación (cualquier string seguro)
- `GEMINI_API_KEY`: API key de Google Gemini

### 3. Configurar la base de datos

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Iniciar el servidor

```bash
python manage.py runserver 0.0.0.0:8000
```

## 🌐 Configurar Webhook de Meta

### Desarrollo Local (con ngrok)

```bash
# Instalar ngrok: https://ngrok.com/
ngrok http 8000
```

Esto te dará una URL pública como: `https://xxxx-xx-xx-xxx-xxx.ngrok.io`

### Configurar en Meta for Developers

1. Ve a tu App en Meta for Developers
2. Navega a WhatsApp > Configuration
3. En **Webhook**, haz clic en "Edit"
4. Ingresa:
   - **Callback URL**: `https://tu-dominio.com/chatbot/webhook/`
   - **Verify Token**: El mismo que pusiste en `META_VERIFY_TOKEN`
5. Suscríbete a los eventos: `messages`

## 📱 Uso

### Enviar mensajes al chatbot

1. Agrega el número de WhatsApp Business a tus contactos
2. Envía cualquier mensaje
3. El bot responderá usando Gemini AI

### Panel de Administración

Accede a `http://localhost:8000/admin/` para:
- Ver historial de conversaciones
- Monitorear mensajes
- Gestionar usuarios

## 🏗️ Estructura del Proyecto

```
whatsapp-chatbot-project/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── whatsapp_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── chatbot/
    ├── __init__.py
    ├── models.py          # Modelos de conversación
    ├── views.py           # Lógica del webhook
    ├── admin.py           # Admin de Django
    ├── apps.py
    ├── services/
    │   ├── whatsapp_service.py  # Cliente API WhatsApp
    │   └── gemini_service.py    # Cliente Gemini AI
    └── management/
        └── commands/
            └── test_bot.py      # Comando para testing
```

## 🔍 Testing

```bash
# Probar conexión con WhatsApp API
python manage.py test_bot

# Ver logs en tiempo real
python manage.py runserver --noreload
```

## 🚀 Despliegue en Producción

### Opción 1: Railway

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login y deploy
railway login
railway init
railway up
```

### Opción 2: Heroku

```bash
heroku create tu-app-name
heroku config:set META_PHONE_NUMBER_ID=xxx
heroku config:set META_ACCESS_TOKEN=xxx
# ... configurar todas las variables
git push heroku main
```

### Opción 3: VPS (Ubuntu)

```bash
# Instalar dependencias
sudo apt update
sudo apt install python3-pip python3-venv nginx

# Configurar con gunicorn + nginx
gunicorn whatsapp_project.wsgi:application --bind 0.0.0.0:8000
```

## 🛠️ Personalización

### Modificar respuestas del bot

Edita `chatbot/services/gemini_service.py`:

```python
def get_response(self, message, context=None):
    prompt = f"""
    Eres un asistente útil de [TU EMPRESA].
    Contexto: {context}
    Usuario: {message}
    """
    # ...
```

### Agregar comandos especiales

En `chatbot/views.py`, agrega lógica personalizada:

```python
if message_text.lower().startswith('/'):
    # Manejar comandos especiales
    if message_text == '/ayuda':
        response = "Comandos disponibles: /ayuda, /info"
```

## 📚 Documentación de APIs

- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Google Gemini API](https://ai.google.dev/docs)
- [Django Documentation](https://docs.djangoproject.com/)

## ⚠️ Notas Importantes

1. **Límites de API**: Meta tiene límites de mensajes. Revisa tu tier.
2. **Seguridad**: Cambia `SECRET_KEY` y `DEBUG=False` en producción.
3. **HTTPS**: Meta requiere HTTPS para webhooks.
4. **Verificación**: El número debe estar verificado en Meta.

## 🐛 Solución de Problemas

### Error: "Webhook verification failed"
- Verifica que `META_VERIFY_TOKEN` coincida en .env y en Meta

### Error: "Invalid access token"
- Regenera el token en Meta for Developers
- Verifica que el token tenga los permisos correctos

### El bot no responde
- Revisa los logs: `python manage.py runserver`
- Verifica que el webhook esté activo en Meta
- Confirma que ngrok/servidor esté accesible

## 📄 Licencia

MIT License - Libre para uso personal y comercial

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor abre un issue o pull request.

## 📧 Soporte

Para problemas o preguntas:
- Revisa la documentación oficial de Meta y Gemini
- Abre un issue en el repositorio
- Consulta los logs del servidor

---

**Desarrollado con ❤️ usando Django, Meta API y Google Gemini**
