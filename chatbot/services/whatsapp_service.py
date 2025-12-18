"""
Servicio para interactuar con WhatsApp Business API
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger('chatbot')


class WhatsAppService:
    """Cliente para WhatsApp Business API de Meta"""
    
    BASE_URL = "https://graph.facebook.com/v22.0"
    
    def __init__(self):
        self.phone_number_id = settings.META_PHONE_NUMBER_ID
        self.access_token = settings.META_ACCESS_TOKEN
        
        if not self.phone_number_id or not self.access_token:
            logger.warning("WhatsApp credentials not configured")
    
    def _get_headers(self):
        """Obtener headers para la API"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def send_text_message(self, to_number, text):
        """
        Enviar mensaje de texto
        
        Args:
            to_number: Número de teléfono del destinatario
            text: Texto del mensaje
        
        Returns:
            message_id si tiene éxito, None en caso de error
        """
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": text
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
            
            data = response.json()
            message_id = data.get('messages', [{}])[0].get('id')
            
            logger.info(f"Mensaje enviado exitosamente: {message_id}")
            return message_id
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error enviando mensaje: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Respuesta de error: {e.response.text}")
            return None
    
    def send_template_message(self, to_number, template_name, language_code='es'):
        """
        Enviar mensaje desde plantilla aprobada
        
        Args:
            to_number: Número de teléfono del destinatario
            template_name: Nombre de la plantilla
            language_code: Código del idioma
        
        Returns:
            message_id si tiene éxito, None en caso de error
        """
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
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
            
            data = response.json()
            message_id = data.get('messages', [{}])[0].get('id')
            
            logger.info(f"Mensaje de plantilla enviado: {message_id}")
            return message_id
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error enviando plantilla: {str(e)}")
            return None
    
    def send_image(self, to_number, image_url, caption=""):
        """
        Enviar imagen
        
        Args:
            to_number: Número de teléfono del destinatario
            image_url: URL de la imagen
            caption: Texto opcional
        
        Returns:
            message_id si tiene éxito, None en caso de error
        """
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption
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
            
            data = response.json()
            message_id = data.get('messages', [{}])[0].get('id')
            
            logger.info(f"Imagen enviada: {message_id}")
            return message_id
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error enviando imagen: {str(e)}")
            return None
    
    def mark_as_read(self, message_id):
        """
        Marcar mensaje como leído
        
        Args:
            message_id: ID del mensaje a marcar
        
        Returns:
            True si tiene éxito, False en caso de error
        """
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return True
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error marcando como leído: {str(e)}")
            return False
    
    def get_media_url(self, media_id):
        """
        Obtener URL de un archivo multimedia
        
        Args:
            media_id: ID del media en WhatsApp
        
        Returns:
            URL del archivo o None
        """
        url = f"{self.BASE_URL}/{media_id}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get('url')
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo URL de media: {str(e)}")
            return None
