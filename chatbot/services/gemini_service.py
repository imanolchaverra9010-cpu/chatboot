"""
Servicio mejorado para interactuar con Google Gemini AI - COMPLETO PARA NEGOCIOS Y MMQ
"""
import logging
import google.generativeai as genai
from django.conf import settings
from .db_service import DatabaseService
from datetime import datetime
import re
import json

logger = logging.getLogger('chatbot')

class GeminiService:
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.db_service = DatabaseService()
        
        if not self.api_key:
            logger.warning("API de Gemini sin configurar")
            return
        
        genai.configure(api_key=self.api_key)
        
        self.generation_config = {
            "temperature": 0.4,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1500,
        }
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=self.generation_config
        )
    
    def _detectar_intencion(self, message):
        """
        Detecta la intención del usuario incluyendo la Media Maratón
        """
        msg_lower = message.lower()
        
        # Prioridad: Detección de la Maratón
        if any(word in msg_lower for word in ['maraton', 'maratón', 'mmq', 'carrera', 'correr', 'quibdo corre']):
            return 'maraton_quibdo'

        intenciones = {
            'buscar_negocio': ['restaurante', 'negocio', 'lugar', 'donde', 'encuentra', 'conoces', 'hay'],
            'buscar_producto': ['producto', 'plato', 'vende', 'menu', 'menú', 'comida', 'precio', 'cuanto cuesta'],
            'horarios': ['horario', 'abierto', 'cerrado', 'abre', 'cierra', 'hora'],
            'resena': ['reseña', 'calificar', 'opinión', 'comentario', 'calificación', 'experiencia'],
            'contacto': ['teléfono', 'telefono', 'whatsapp', 'contacto', 'llamar', 'numero', 'número'],
            'ubicacion': ['dirección', 'direccion', 'ubicación', 'ubicacion', 'cómo llegar', 'como llegar', 'donde queda'],
            'categorias': ['categoría', 'categoria', 'tipo', 'qué hay', 'que hay', 'opciones']
        }
        
        for intencion, palabras_clave in intenciones.items():
            if any(palabra in msg_lower for palabra in palabras_clave):
                return intencion
        
        return 'general'

    def _obtener_info_maraton(self):
        """
        Base de datos estática para la Media Maratón de Quibdó
        """
        return """
        INFORMACIÓN MEDIA MARATÓN QUIBDÓ (MMQ):
        - Descripción: Evento deportivo urbano para cultivar la paz, bienestar y estilos de vida saludables.
        - Misión: Fomentar cultura deportiva, salud física y mental, y visibilizar gimnasios/grupos al aire libre.
        - Visión: Ser impulsores líderes de hábitos saludables con valores de respeto y tolerancia.
        - Rutas: 5 Kilómetros, 10 Kilómetros y 21 Kilómetros.
        - Categorías: Infantil (2-15 años), Juvenil (16-19), Abierta (20-49), Élite (Mayores de 18) y Máster (50+ años).
        - Géneros: Masculino, Femenino y Niños.
        - Fecha del evento: Domingo, 14 de junio de 2026.
        - Ubicación: Quibdó, Chocó, Colombia.
        - Inscripciones: Abiertas del 26/11/2025 al 31/12/2025.
        - Costo: $ 120.000 para todas las categorías.
        - Beneficio Preventa: Los inscritos antes del 31 de diciembre de 2025 recibirán un obsequio especial.
        - El KIT incluye: Camiseta, Medalla, Dorsal, Chip e Hidratación.
        - Sitio Web Oficial: https://mediamaratondequibdo.com/eventos/
        - Link de Inscripción: https://respira.run/media-maraton-quibdo
        """

    def _extraer_informacion_negocios(self, message, intencion='general'):
        context = ""
        msg_clean = message.lower().strip()
        
        # Normalizar texto para búsqueda en DB
        msg_normalized = re.sub(r'(restaurantes|comiditas|sitios de comida)', 'restaurante', msg_clean)
        
        try:
            if intencion == 'resena':
                context += "\n\n📝 **SISTEMA DE RESEÑAS:** Pide nombre de negocio, estrellas (1-5) y comentario.\n"
            
            if intencion == 'categorias':
                categorias = self.db_service.obtener_categorias_negocios()
                if categorias:
                    context += "\n🏷️ CATEGORÍAS: " + ", ".join([str(c) for c in categorias]) + "\n"

            negocios = self.db_service.buscar_negocios(query=msg_clean, limit=5)
            if negocios:
                context += "\n🏪 NEGOCIOS ENCONTRADOS:\n"
                for neg in negocios:
                    estado = self.db_service.verificar_negocio_abierto(neg.id)
                    context += f"- {neg.nombre.upper()} ({neg.categoria}): {estado['mensaje']}. Dir: {neg.direccion}. Tel: {neg.telefono}\n"
        
        except Exception as e:
            logger.error(f"Error extrayendo info de negocios: {e}")
        
        return context

    def _procesar_resena(self, message, phone_number):
        try:
            negocios = self.db_service.buscar_negocios(query=message, limit=1)
            if not negocios:
                return None, "No encontré el negocio. ¿Cómo se llama exactamente?"
            
            calificacion_match = re.search(r'\b([1-5])\b', message)
            if not calificacion_match:
                return negocios[0], "encontrado_sin_calificacion"
            
            calificacion = int(calificacion_match.group(1))
            resena = self.db_service.crear_resena(
                negocio_id=negocios[0].id,
                telefono_cliente=phone_number,
                calificacion=calificacion,
                comentario=message
            )
            return negocios[0], f"resena_creada_{calificacion}" if resena else "error_creando_resena"
        except Exception:
            return None, "error"

    def get_response(self, message, context=None, phone_number=None):
        if not self.api_key:
            return "Lo siento, manit@, el servicio no está listo."

        try:
            intencion = self._detectar_intencion(message)
            info_maraton = self._obtener_info_maraton() if intencion == 'maraton_quibdo' else ""
            
            # Lógica de Reseñas
            if intencion == 'resena' and any(word in message.lower() for word in ['calificar', 'reseña']):
                negocio, resultado = self._procesar_resena(message, phone_number)
                if resultado == "encontrado_sin_calificacion":
                    return f"¡Listo, manit@! ¿Cuántas estrellas (1-5) le das a **{negocio.nombre}**?"
                if "resena_creada" in resultado:
                    return f"¡Maunifik! Tu reseña para **{negocio.nombre}** ya quedó guardada. ¡Gracias, ve coco!"

            db_context = self._extraer_informacion_negocios(message, intencion)
            hora_actual = datetime.now().strftime("%I:%M %p")
            
            system_prompt = """Eres Luisa, la asistente virtual de Parchaoo. Eres chocoana, amable, eficiente y usas jerga local.

**CONTEXTO DE LA MEDIA MARATÓN QUIBDÓ (MMQ):**
{info_maraton}

**INFORMACIÓN DE NEGOCIOS:**
{db_context}

**REGLAS DE ORO:**
1. Si el usuario pregunta por la Media Maratón (MMQ), usa los datos específicos: fecha (14 de junio 2026), rutas (5K, 10K, 21K) y costo ($120.000).
2. ¡IMPORTANTE!: Si preguntan por inscripciones, diles que son hasta el 31 de diciembre de 2025 para recibir el OBSEQUIO ESPECIAL.
3. Si preguntan por el sitio web o dónde inscribirse, entrega los links correspondientes.
4. Usa lenguaje del Chocó: "¡Q hubo!, manit@".
5. Si no sabes algo de un negocio, sugiere llamar o escribir a su WhatsApp.

**HORA ACTUAL:** {hora_actual}
**MENSAJE DEL USUARIO:** "{message}"
"""
            prompt = system_prompt.format(
                info_maraton=info_maraton,
                db_context=db_context if db_context else "No hay info específica de negocios.",
                hora_actual=hora_actual,
                message=message
            )
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        
        except Exception as e:
            logger.error(f"Error en GeminiService: {e}")
            return "¡Ey, manit@! Se me cruzaron los cables. ¿Me repites porfa?"
