"""
Servicio para interactuar con Google Gemini AI - ESPECIALIZADO EN NEGOCIOS
"""
import logging
import google.generativeai as genai
from django.conf import settings
from .db_service import DatabaseService
from datetime import datetime
import re

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
            "temperature": 0.4, # Bajamos la temperatura para que sea menos "creativo" y más preciso
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash", # Actualizado a la versión más reciente y rápida
            generation_config=self.generation_config
        )
    
    def _extraer_informacion_negocios(self, message):
        """
        Extraer información relevante de negocios siendo más flexible con la búsqueda
        """
        context = ""
        # Limpieza básica para mejorar coincidencia
        msg_clean = message.lower().strip()
        # Normalizar plurales comunes en Quibdó
        msg_normalized = re.sub(r'(restaurantes|comiditas|sitios de comida)', 'restaurante', msg_clean)
        msg_normalized = re.sub(r'(farmacias|droguerias)', 'farmacia', msg_normalized)
        msg_normalized = re.sub(r'(tiendas|supermercados|mercados)', 'supermercado', msg_normalized)
        
        try:
            # 1. BÚSQUEDA POR CATEGORÍA (Prioridad alta)
            categorias_disponibles = self.db_service.obtener_categorias_negocios()
            categoria_encontrada = None
            
            # Verificar si el usuario mencionó una categoría existente
            for cat in categorias_disponibles:
                nombre_cat = cat.nombre.lower() if hasattr(cat, 'nombre') else str(cat).lower()
                if nombre_cat in msg_normalized:
                    categoria_encontrada = nombre_cat
                    break

            # 2. OBTENER NEGOCIOS (Si hay categoría o palabras de búsqueda)
            negocios = self.db_service.buscar_negocios(
                query=None if categoria_encontrada else msg_clean,
                categoria=categoria_encontrada,
                limit=10
            )
            
            if negocios:
                context += "\n\n🏪 **NEGOCIOS ENCONTRADOS EN LA BASE DE DATOS:**\n"
                for neg in negocios:
                    estado = self.db_service.verificar_negocio_abierto(neg.id)
                    emoji_estado = "🟢 ABIERTO" if estado['abierto'] else "🔴 CERRADO"
                    
                    context += f"- {neg.nombre.upper()} "
                    context += f"({neg.categoria if neg.categoria else 'General'})\n"
                    context += f"  📍 Ubicación: {neg.direccion} {f'- {neg.barrio}' if neg.barrio else ''}\n"
                    context += f"  📞 Tel: {neg.telefono if neg.telefono else 'No registrado'}\n"
                    context += f"  ⌚ Estado: {emoji_estado} ({estado['mensaje']})\n\n"
            
            # 3. LISTADO DE CATEGORÍAS (Si el usuario pregunta qué hay o qué hace el bot)
            if any(kw in msg_clean for kw in ['categoría', 'categoria', 'qué hay', 'que hay', 'haces', 'lista']):
                if categorias_disponibles:
                    context += "\n\n🏷️ **CATEGORÍAS DISPONIBLES QUE PUEDES CONSULTAR:**\n"
                    context += ", ".join([c.nombre if hasattr(c, 'nombre') else str(c) for c in categorias_disponibles])
                    context += "\n"

        except Exception as e:
            logger.error(f"Error extrayendo información: {e}")
        
        return context
    
    def get_response(self, message, context=None, phone_number=None):
        if not self.api_key:
            return "Lo siento, manit@, el servicio no está listo."

        try:
            db_context = self._extraer_informacion_negocios(message)
            hora_actual = datetime.now().strftime("%I:%M %p")
            
            # System Prompt mucho más directo y "menos tímido"
            system_prompt = """Eres Luisa, la asistente virtual de parchaoo más eficiente de Quibdó. 
Tu estilo es chocoano, cercano y muy servicial, pero sobre todo DIRECTO.

**REGLAS DE ORO:**
1. Si en la 'INFORMACIÓN DE LA BASE DE DATOS' hay negocios, DEBES listarlos de inmediato. No digas "no tengo la lista completa", usa lo que tienes ahí.
2. Usa expresiones como "¡Q hubo!", "Vea, manit@", "Con gusto, parche, ve coco, dejá así, maunifik".
3. Si el negocio está abierto, anímalo a ir. Si está cerrado, sugiere que llame o espere a que abran.
4. Formato de precios: $50.000.
5. Si no hay datos en la sección de abajo, SOLO ENTONCES di que no lo tienes mapeado aún y pide detalles.

**INFORMACIÓN DE LA BASE DE DATOS (ESTO ES LO QUE SABES):**
{db_context}

**CONTEXTO TEMPORAL:**
Hora: {hora_actual}

**CONVERSACIÓN ANTERIOR:**
{context}

**TAREA:** Responde al usuario "{message}" de forma entusiasta usando los datos de arriba."""

            prompt = system_prompt.format(
                db_context=db_context if db_context else "No hay negocios específicos para esta búsqueda. Dile que te dé más detalles.",
                hora_actual=hora_actual,
                context=context if context else "Primer mensaje",
                message=message
            )
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        
        except Exception as e:
            logger.error(f"Error en Gemini: {e}")
            return "¡Ey, manit@! Se me cruzaron los cables. ¿Me repites porfa?"
