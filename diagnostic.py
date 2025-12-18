"""
Script de diagnóstico para WhatsApp Chatbot
Ejecuta: python diagnostic.py
"""

import os
import sys
import requests
from pathlib import Path

# Agregar el proyecto al path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_project.settings')
import django
django.setup()

from django.conf import settings
from chatbot.models import Conversation, Message

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def check_mark(condition):
    return "✅" if condition else "❌"

def main():
    print("\n" + "🔍 DIAGNÓSTICO DEL CHATBOT DE WHATSAPP" + "\n")
    
    # 1. Variables de Entorno
    print_section("1. VARIABLES DE ENTORNO")
    
    checks = [
        ("SECRET_KEY", bool(settings.SECRET_KEY), "Configurada"),
        ("DEBUG", settings.DEBUG, f"Modo: {'Desarrollo' if settings.DEBUG else 'Producción'}"),
        ("META_VERIFY_TOKEN", bool(settings.META_VERIFY_TOKEN), settings.META_VERIFY_TOKEN),
        ("META_PHONE_NUMBER_ID", bool(settings.META_PHONE_NUMBER_ID), 
         settings.META_PHONE_NUMBER_ID if settings.META_PHONE_NUMBER_ID else "NO CONFIGURADO"),
        ("META_ACCESS_TOKEN", bool(settings.META_ACCESS_TOKEN), 
         f"{settings.META_ACCESS_TOKEN[:20]}..." if settings.META_ACCESS_TOKEN else "NO CONFIGURADO"),
        ("GEMINI_API_KEY", bool(settings.GEMINI_API_KEY),
         f"{settings.GEMINI_API_KEY[:20]}..." if settings.GEMINI_API_KEY else "NO CONFIGURADO"),
        ("NGROK_DOMAIN", bool(settings.NGROK_DOMAIN),
         settings.NGROK_DOMAIN if settings.NGROK_DOMAIN else "NO CONFIGURADO"),
    ]
    
    for name, condition, value in checks:
        print(f"{check_mark(condition)} {name:25s} : {value}")
    
    # 2. Configuración de Django
    print_section("2. CONFIGURACIÓN DE DJANGO")
    
    print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"✅ BASE_DIR: {settings.BASE_DIR}")
    print(f"✅ Database: {settings.DATABASES['default']['ENGINE']}")
    
    # 3. Base de Datos
    print_section("3. BASE DE DATOS")
    
    try:
        conversations_count = Conversation.objects.count()
        messages_count = Message.objects.count()
        print(f"✅ Conversaciones en BD: {conversations_count}")
        print(f"✅ Mensajes en BD: {messages_count}")
        
        if conversations_count > 0:
            last_conv = Conversation.objects.first()
            print(f"📱 Última conversación: {last_conv.phone_number} ({last_conv.updated_at})")
    except Exception as e:
        print(f"❌ Error accediendo a la BD: {e}")
    
    # 4. Conectividad Local
    print_section("4. CONECTIVIDAD LOCAL")
    
    local_urls = [
        "http://127.0.0.1:8000/chatbot/",
        "http://127.0.0.1:8000/chatbot/status/",
        "http://127.0.0.1:8000/chatbot/webhook/",
    ]
    
    for url in local_urls:
        try:
            response = requests.get(url, timeout=2)
            print(f"{check_mark(response.status_code == 200)} {url} - Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {url} - No se pudo conectar (¿Servidor corriendo?)")
        except Exception as e:
            print(f"❌ {url} - Error: {str(e)}")
    
    # 5. Ngrok
    print_section("5. NGROK")
    
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            if tunnels:
                for tunnel in tunnels:
                    public_url = tunnel.get('public_url', '')
                    print(f"✅ Túnel activo: {public_url}")
                    print(f"   👉 URL para Meta: {public_url}/chatbot/webhook/")
            else:
                print("❌ Ngrok está corriendo pero no hay túneles activos")
        else:
            print(f"❌ Ngrok respondió con status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ No se pudo conectar a ngrok en http://localhost:4040")
        print("   Asegúrate de que ngrok esté corriendo: ngrok http 8000")
    except Exception as e:
        print(f"❌ Error verificando ngrok: {e}")
    
    # 6. Test del Webhook
    print_section("6. TEST DEL WEBHOOK")
    
    if settings.NGROK_DOMAIN:
        webhook_url = f"https://{settings.NGROK_DOMAIN}/chatbot/webhook/"
        test_url = f"{webhook_url}?hub.mode=subscribe&hub.verify_token={settings.META_VERIFY_TOKEN}&hub.challenge=TEST123"
        
        print(f"🔗 URL del webhook: {webhook_url}")
        print(f"🧪 URL de prueba: {test_url}")
        
        try:
            response = requests.get(test_url, timeout=5)
            if response.status_code == 200 and response.text == "TEST123":
                print(f"✅ Webhook verificado correctamente!")
            else:
                print(f"❌ Webhook no verificó correctamente")
                print(f"   Status: {response.status_code}")
                print(f"   Respuesta: {response.text[:100]}")
        except Exception as e:
            print(f"❌ Error probando webhook: {e}")
    else:
        print("❌ NGROK_DOMAIN no está configurado en .env")
    
    # 7. Recomendaciones
    print_section("7. RECOMENDACIONES")
    
    issues = []
    
    if not settings.META_PHONE_NUMBER_ID:
        issues.append("Configura META_PHONE_NUMBER_ID en tu archivo .env")
    
    if not settings.META_ACCESS_TOKEN:
        issues.append("Configura META_ACCESS_TOKEN en tu archivo .env")
    
    if not settings.GEMINI_API_KEY:
        issues.append("Configura GEMINI_API_KEY en tu archivo .env")
    
    if not settings.NGROK_DOMAIN:
        issues.append("Configura NGROK_DOMAIN en tu archivo .env con tu URL de ngrok")
    
    if issues:
        print("⚠️  Problemas encontrados:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("✅ No se encontraron problemas obvios de configuración")
    
    # 8. Próximos Pasos
    print_section("8. PRÓXIMOS PASOS")
    
    print("""
1. Asegúrate de que Django esté corriendo:
   python manage.py runserver

2. Asegúrate de que ngrok esté corriendo:
   ngrok http 8000

3. Copia la URL de ngrok y actualízala en:
   - Tu archivo .env (NGROK_DOMAIN)
   - Panel de Meta (Configuración del Webhook)

4. Verifica que en Meta el webhook esté suscrito a 'messages'

5. Envía un mensaje de prueba desde WhatsApp

6. Revisa los logs de Django para ver si llega el webhook
    """)
    
    print("\n" + "="*70)
    print("  FIN DEL DIAGNÓSTICO")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
