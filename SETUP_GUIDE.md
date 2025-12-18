# Guía de Configuración Detallada

## 📱 Configuración de Meta for Developers

### Paso 1: Crear App en Meta

1. Ve a https://developers.facebook.com/
2. Haz clic en "Mis Apps" > "Crear App"
3. Selecciona "Negocio" como tipo
4. Completa la información:
   - Nombre de la app: "Mi Chatbot WhatsApp"
   - Email de contacto
   - Propósito del negocio

### Paso 2: Agregar WhatsApp a tu App

1. En el dashboard de tu app, busca "WhatsApp"
2. Haz clic en "Configurar"
3. Selecciona o crea un perfil de negocio

### Paso 3: Obtener Credenciales

#### Phone Number ID:
1. Ve a WhatsApp > API Setup
2. Copia el "Phone number ID" (número largo)
3. Guárdalo para el archivo `.env` como `META_PHONE_NUMBER_ID`

#### Access Token:
1. En la misma página (API Setup), verás "Temporary access token"
2. **IMPORTANTE**: Este token es temporal (24 horas)
3. Para producción, genera un token permanente:
   - Ve a "Configuración" > "Básico"
   - Genera un token de acceso del sistema
4. Guárdalo como `META_ACCESS_TOKEN`

#### Verify Token:
1. Crea tu propio token (cualquier string seguro)
2. Ejemplo: `mi_token_super_secreto_12345`
3. Guárdalo como `META_VERIFY_TOKEN`

### Paso 4: Número de Prueba

Meta te proporciona un número de prueba automáticamente:
- Puedes agregar hasta 5 números para pruebas
- Ve a WhatsApp > API Setup > "To"
- Agrega tu número de WhatsApp personal

### Paso 5: Configurar Webhook (después de iniciar el servidor)

1. Inicia tu servidor local con ngrok:
   ```bash
   ngrok http 8000
   ```

2. Copia la URL de ngrok (ej: `https://xxxx.ngrok.io`)

3. En Meta for Developers:
   - Ve a WhatsApp > Configuration
   - Haz clic en "Edit" en Webhook
   - Callback URL: `https://xxxx.ngrok.io/chatbot/webhook/`
   - Verify token: Tu `META_VERIFY_TOKEN`
   - Haz clic en "Verify and save"

4. Suscríbete a eventos de webhook:
   - Marca "messages"
   - Guarda cambios

## 🤖 Configuración de Google Gemini

### Paso 1: Obtener API Key

1. Ve a https://makersuite.google.com/app/apikey
2. Inicia sesión con tu cuenta de Google
3. Haz clic en "Create API Key"
4. Selecciona un proyecto de Google Cloud (o crea uno nuevo)
5. Copia la API key generada
6. Guárdala como `GEMINI_API_KEY`

### Límites Gratuitos de Gemini:

- 60 solicitudes por minuto
- 1,500 solicitudes por día
- Gratis para uso moderado

## 🔧 Instalación Local Paso a Paso

### Requisitos Previos

```bash
# Verificar Python
python --version  # Debe ser 3.8 o superior

# Verificar pip
pip --version
```

### Instalación

1. **Extraer el proyecto**
   ```bash
   unzip whatsapp-chatbot-project.zip
   cd whatsapp-chatbot-project
   ```

2. **Crear entorno virtual**
   ```bash
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   nano .env  # o usa tu editor favorito
   ```
   
   Completa TODAS las variables:
   ```env
   META_PHONE_NUMBER_ID=123456789012345
   META_ACCESS_TOKEN=EAAxxxxxxxxxxxxx
   META_VERIFY_TOKEN=mi_token_seguro_12345
   GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxx
   SECRET_KEY=django-insecure-genera-uno-nuevo-aqui
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

5. **Configurar base de datos**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Crear superusuario**
   ```bash
   python manage.py createsuperuser
   # Username: admin
   # Email: tu@email.com
   # Password: ********
   ```

7. **Probar la configuración**
   ```bash
   python manage.py test_bot
   ```

8. **Iniciar servidor**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

9. **Exponer con ngrok** (en otra terminal)
   ```bash
   # Descargar ngrok: https://ngrok.com/download
   ngrok http 8000
   ```

## 🌐 Configuración del Webhook

### Verificar que el webhook funciona:

1. Servidor corriendo en `http://localhost:8000`
2. Ngrok exponiendo en `https://xxxx.ngrok.io`
3. Webhook configurado en Meta

### Probar manualmente:

```bash
# Test de verificación (debe devolver el challenge)
curl "http://localhost:8000/chatbot/webhook/?hub.mode=subscribe&hub.verify_token=tu_verify_token&hub.challenge=CHALLENGE"
```

### Logs en tiempo real:

```bash
# En tu terminal con el servidor
python manage.py runserver

# Verás algo como:
# [INFO] Webhook recibido: {...}
# [INFO] Procesando mensaje xyz de +1234567890
```

## 📧 Probar el Bot

### Desde WhatsApp:

1. Abre WhatsApp en tu teléfono
2. Busca el número de prueba de Meta
3. Envía cualquier mensaje
4. ¡El bot debe responder!

### Comandos de prueba:

```bash
# Probar solo Gemini
python manage.py test_bot

# Probar envío de WhatsApp (reemplaza con tu número)
python manage.py test_bot --phone +1234567890

# Mensaje personalizado
python manage.py test_bot --phone +1234567890 --message "Hola bot"
```

## 🔍 Solución de Problemas Comunes

### Error: "Invalid access token"

**Solución:**
1. Verifica que el token esté completo (sin espacios)
2. Genera un nuevo token en Meta
3. Actualiza el `.env`
4. Reinicia el servidor

### Error: "Webhook verification failed"

**Solución:**
1. Verifica que `META_VERIFY_TOKEN` en `.env` sea exactamente igual al que pusiste en Meta
2. Verifica que la URL del webhook termine en `/chatbot/webhook/`
3. Asegúrate que ngrok esté corriendo

### El bot no responde

**Checklist:**
- [ ] Servidor de Django corriendo
- [ ] Ngrok exponiendo el servidor
- [ ] Webhook configurado correctamente en Meta
- [ ] Webhook suscrito a eventos "messages"
- [ ] Número agregado a la lista de prueba
- [ ] Variables de entorno correctas

**Ver logs:**
```bash
python manage.py runserver
# Observa la terminal cuando envíes un mensaje
```

### Error: "No module named 'google.generativeai'"

**Solución:**
```bash
pip install --upgrade google-generativeai
```

### Error de CORS o CSRF

**Solución:**
El webhook está excluido de CSRF. Si tienes problemas:
```python
# En settings.py
CSRF_TRUSTED_ORIGINS = ['https://tu-dominio-ngrok.ngrok.io']
```

## 🚀 Despliegue en Producción

### Railway (Recomendado)

```bash
# Instalar CLI
npm i -g @railway/cli

# Login
railway login

# Crear proyecto
railway init

# Configurar variables
railway variables set META_PHONE_NUMBER_ID=xxx
railway variables set META_ACCESS_TOKEN=xxx
railway variables set META_VERIFY_TOKEN=xxx
railway variables set GEMINI_API_KEY=xxx
railway variables set SECRET_KEY=xxx
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=tu-app.railway.app

# Deploy
railway up
```

### Heroku

```bash
# Login
heroku login

# Crear app
heroku create mi-chatbot-whatsapp

# Configurar variables
heroku config:set META_PHONE_NUMBER_ID=xxx
heroku config:set META_ACCESS_TOKEN=xxx
# ... todas las demás

# Deploy
git add .
git commit -m "Initial commit"
git push heroku main

# Migrar DB
heroku run python manage.py migrate

# Crear superuser
heroku run python manage.py createsuperuser
```

### VPS (DigitalOcean, AWS, etc.)

```bash
# Conectar por SSH
ssh user@tu-servidor

# Instalar dependencias
sudo apt update
sudo apt install python3-pip python3-venv nginx

# Clonar proyecto
git clone tu-repo
cd whatsapp-chatbot-project

# Configurar
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Variables de entorno
nano .env

# Migrar
python manage.py migrate
python manage.py collectstatic

# Gunicorn
gunicorn whatsapp_project.wsgi:application --bind 0.0.0.0:8000 --daemon

# Nginx
sudo nano /etc/nginx/sites-available/chatbot
# Configurar proxy reverso a :8000

sudo ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## 🔒 Seguridad en Producción

1. **Cambiar SECRET_KEY**:
   ```python
   # Generar nueva clave
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **DEBUG=False**

3. **ALLOWED_HOSTS**:
   ```env
   ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
   ```

4. **HTTPS obligatorio**:
   ```python
   # settings.py
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ```

5. **Variables de entorno**:
   - Nunca commits el archivo `.env`
   - Usa secretos del hosting (Railway/Heroku)

## 📊 Monitoreo

### Ver conversaciones:
```
http://tu-dominio.com/admin/
```

### Logs en producción:
```bash
# Heroku
heroku logs --tail

# Railway
railway logs

# VPS
tail -f /var/log/nginx/error.log
```

## 🆘 Soporte

- **Documentación Meta**: https://developers.facebook.com/docs/whatsapp
- **Documentación Gemini**: https://ai.google.dev/docs
- **Django Docs**: https://docs.djangoproject.com/

---

**¿Problemas? Revisa los logs y verifica la configuración paso a paso.**
