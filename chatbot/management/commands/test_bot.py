"""
Comando para probar el bot
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from chatbot.services.whatsapp_service import WhatsAppService
from chatbot.services.gemini_service import GeminiService


class Command(BaseCommand):
    help = 'Prueba las conexiones del bot con WhatsApp y Gemini'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            help='Número de teléfono para enviar mensaje de prueba (con código de país)',
        )
        parser.add_argument(
            '--message',
            type=str,
            default='Hola, este es un mensaje de prueba',
            help='Mensaje de prueba a enviar',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Test del Bot de WhatsApp ===\n'))
        
        # Verificar configuración
        self.stdout.write('1. Verificando configuración...')
        self.check_configuration()
        
        # Probar Gemini
        self.stdout.write('\n2. Probando Gemini AI...')
        self.test_gemini()
        
        # Probar WhatsApp (opcional)
        phone = options.get('phone')
        if phone:
            self.stdout.write('\n3. Probando WhatsApp API...')
            message = options.get('message')
            self.test_whatsapp(phone, message)
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\n3. Test de WhatsApp omitido (usa --phone para probar)'
                )
            )
        
        self.stdout.write(self.style.SUCCESS('\n=== Test completado ==='))
    
    def check_configuration(self):
        """Verificar que las variables de entorno estén configuradas"""
        checks = {
            'META_PHONE_NUMBER_ID': settings.META_PHONE_NUMBER_ID,
            'META_ACCESS_TOKEN': settings.META_ACCESS_TOKEN,
            'META_VERIFY_TOKEN': settings.META_VERIFY_TOKEN,
            'GEMINI_API_KEY': settings.GEMINI_API_KEY,
        }
        
        all_ok = True
        for key, value in checks.items():
            if value:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ {key}: Configurado')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ {key}: NO configurado')
                )
                all_ok = False
        
        if all_ok:
            self.stdout.write(self.style.SUCCESS('  Todas las variables configuradas'))
        else:
            self.stdout.write(
                self.style.WARNING('  Algunas variables no están configuradas')
            )
    
    def test_gemini(self):
        """Probar la conexión con Gemini"""
        try:
            gemini = GeminiService()
            response = gemini.get_response("Di 'Hola' en una palabra")
            
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ Gemini responde: "{response}"')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Error con Gemini: {str(e)}')
            )
    
    def test_whatsapp(self, phone, message):
        """Probar el envío de mensaje por WhatsApp"""
        try:
            whatsapp = WhatsAppService()
            message_id = whatsapp.send_text_message(phone, message)
            
            if message_id:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Mensaje enviado exitosamente (ID: {message_id})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR('  ✗ No se pudo enviar el mensaje')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Error enviando mensaje: {str(e)}')
            )
