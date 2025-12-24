"""
Servicio mejorado para interactuar con Google Gemini AI - COMPLETO PARA NEGOCIOS
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
        Detecta la intención del usuario para respuestas más precisas
        """
        msg_lower = message.lower()
        
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
    
    def _extraer_informacion_negocios(self, message, intencion='general'):
        """
        Extrae información relevante de negocios de forma inteligente según la intención
        """
        context = ""
        msg_clean = message.lower().strip()
        
        # Normalizar texto
        msg_normalized = re.sub(r'(restaurantes|comiditas|sitios de comida)', 'restaurante', msg_clean)
        msg_normalized = re.sub(r'(farmacias|droguerias)', 'farmacia', msg_normalized)
        msg_normalized = re.sub(r'(tiendas|supermercados|mercados)', 'supermercado', msg_normalized)
        
        try:
            # INTENCIÓN: RESEÑA
            if intencion == 'resena':
                context += "\n\n📝 **SISTEMA DE RESEÑAS DISPONIBLE:**\n"
                context += "Para dejar una reseña, dime:\n"
                context += "1. El nombre del negocio\n"
                context += "2. Tu calificación (1-5 estrellas)\n"
                context += "3. Tu comentario (opcional)\n"
                context += "Ejemplo: 'Quiero calificar a BOGA con 5 estrellas, excelente comida'\n\n"
            
            # INTENCIÓN: CATEGORÍAS
            if intencion == 'categorias' or any(word in msg_clean for word in ['categoría', 'categoria', 'qué hay', 'que hay']):
                categorias = self.db_service.obtener_categorias_negocios()
                if categorias:
                    context += "\n\n🏷️ **CATEGORÍAS DISPONIBLES:**\n"
                    context += ", ".join([c.nombre if hasattr(c, 'nombre') else str(c) for c in categorias])
                    context += "\n\n"
            
            # BUSCAR CATEGORÍA ESPECÍFICA
            categorias_disponibles = self.db_service.obtener_categorias_negocios()
            categoria_encontrada = None
            
            for cat in categorias_disponibles:
                nombre_cat = cat.nombre.lower() if hasattr(cat, 'nombre') else str(cat).lower()
                if nombre_cat in msg_normalized:
                    categoria_encontrada = nombre_cat
                    break
            
            # OBTENER NEGOCIOS
            negocios = self.db_service.buscar_negocios(
                query=None if categoria_encontrada else msg_clean,
                categoria=categoria_encontrada,
                limit=10
            )
            
            if negocios:
                context += "\n\n🏪 **NEGOCIOS ENCONTRADOS:**\n"
                for neg in negocios:
                    # Información básica del negocio
                    context += f"\n**{neg.nombre.upper()}**"
                    if neg.verificado:
                        context += " ✅ (Verificado)"
                    context += f"\n📂 {neg.categoria if neg.categoria else 'General'}\n"
                    
                    # Estado de apertura
                    if intencion in ['horarios', 'general', 'buscar_negocio']:
                        estado = self.db_service.verificar_negocio_abierto(neg.id)
                        emoji_estado = "🟢 ABIERTO" if estado['abierto'] else "🔴 CERRADO"
                        context += f"⏰ Estado: {emoji_estado} - {estado['mensaje']}\n"
                    
                    # Ubicación
                    if intencion in ['ubicacion', 'general', 'buscar_negocio']:
                        context += f"📍 Dirección: {neg.direccion}"
                        if neg.barrio:
                            context += f" - {neg.barrio}"
                        context += "\n"
                        if neg.referencia_ubicacion:
                            context += f"🗺️ Referencia: {neg.referencia_ubicacion}\n"
                    
                    # Contacto
                    if intencion in ['contacto', 'general', 'buscar_negocio']:
                        if neg.telefono:
                            context += f"📞 Teléfono: {neg.telefono}\n"
                        if neg.whatsapp:
                            context += f"💬 WhatsApp: {neg.whatsapp}\n"
                    
                    # Productos/Menú
                    if intencion in ['buscar_producto', 'general']:
                        productos = self.db_service.obtener_productos_negocio(neg.id, limit=5)
                        if productos:
                            context += f"🍽️ Algunos productos destacados:\n"
                            for prod in productos:
                                context += f"  • {prod.nombre}"
                                if prod.precio:
                                    context += f" - {prod.get_precio_display()}"
                                context += "\n"
                    
                    # Reseñas y calificación
                    calificacion = self.db_service.obtener_calificacion_promedio(neg.id)
                    if calificacion:
                        estrellas = "⭐" * int(round(calificacion))
                        context += f"⭐ Calificación: {calificacion:.1f}/5 {estrellas}\n"
                    
                    context += "\n"
            
            # BUSCAR PRODUCTOS ESPECÍFICOS
            if intencion == 'buscar_producto' and not negocios:
                # Buscar en todos los negocios
                context += "\n\n🔍 **BUSCANDO PRODUCTOS...**\n"
                palabras_busqueda = msg_clean.split()
                for palabra in palabras_busqueda:
                    if len(palabra) > 3:  # Solo palabras significativas
                        from ..models import ProductoNegocio
                        productos = ProductoNegocio.objects.filter(
                            nombre__icontains=palabra,
                            activo=True,
                            disponible=True
                        ).select_related('negocio')[:10]
                        
                        if productos:
                            context += f"\nProductos con '{palabra}':\n"
                            for prod in productos:
                                context += f"• {prod.nombre} - {prod.get_precio_display()}\n"
                                context += f"  En: {prod.negocio.nombre}\n"
        
        except Exception as e:
            logger.error(f"Error extrayendo información: {e}")
        
        return context
    
    def _procesar_resena(self, message, phone_number):
        """
        Procesa una reseña del usuario
        """
        try:
            # Extraer nombre del negocio
            negocios = self.db_service.buscar_negocios(query=message, limit=5)
            
            if not negocios:
                return None, "No encontré el negocio que mencionas. ¿Puedes ser más específico?"
            
            # Extraer calificación (buscar números del 1-5)
            calificacion_match = re.search(r'\b([1-5])\b', message)
            estrellas_match = re.search(r'(\d+)\s*estrella', message.lower())
            
            calificacion = None
            if calificacion_match:
                calificacion = int(calificacion_match.group(1))
            elif estrellas_match:
                calificacion = int(estrellas_match.group(1))
            
            if not calificacion:
                return negocios[0], "encontrado_sin_calificacion"
            
            # Extraer comentario (el resto del texto)
            comentario = message
            
            # Crear reseña
            negocio = negocios[0]
            resena = self.db_service.crear_resena(
                negocio_id=negocio.id,
                telefono_cliente=phone_number,
                calificacion=calificacion,
                comentario=comentario
            )
            
            if resena:
                return negocio, f"resena_creada_{calificacion}"
            
            return negocio, "error_creando_resena"
            
        except Exception as e:
            logger.error(f"Error procesando reseña: {e}")
            return None, "error"
    
    def get_response(self, message, context=None, phone_number=None):
        if not self.api_key:
            return "Lo siento, manit@, el servicio no está listo."

        try:
            # Detectar intención
            intencion = self._detectar_intencion(message)
            
            # Procesar reseñas
            if intencion == 'resena' and any(word in message.lower() for word in ['calificar', 'reseña', 'opinión']):
                negocio, resultado = self._procesar_resena(message, phone_number)
                
                if resultado == "error":
                    return "Hubo un error procesando tu reseña. Intenta de nuevo."
                elif resultado == "encontrado_sin_calificacion":
                    return f"¡Perfecto! Quieres calificar **{negocio.nombre}**. ¿Cuántas estrellas le das? (1-5)"
                elif "resena_creada" in resultado:
                    calificacion = resultado.split('_')[-1]
                    return f"¡Maunifik! Tu reseña de **{calificacion} estrellas** para **{negocio.nombre}** ha sido recibida. ¡Será revisada pronto! ¡Gracias por tu opinión, ve coco!"
                elif resultado == "error_creando_resena":
                    return "No pude guardar tu reseña. ¿Puedes intentar de nuevo?"
                else:
                    return resultado
            
            # Extraer información de la base de datos
            db_context = self._extraer_informacion_negocios(message, intencion)
            hora_actual = datetime.now().strftime("%I:%M %p")
            
            # System Prompt adaptado a la intención
            system_prompt = """Eres Luisa, la asistente virtual de Parchaoo, super eficiente y chocoana.

**INFORMACIÓN IMPORTANTE:**
{db_context}

**HORA ACTUAL:** {hora_actual}

**CONTEXTO DE CONVERSACIÓN:**
{context}

**INTENCIÓN DETECTADA:** {intencion}

**REGLAS:**
1. Si hay información en "INFORMACIÓN IMPORTANTE", úsala SIEMPRE.
2. Sé directa, amable y usa lenguaje chocoano (¡Q hubo!, manit@, ve coco, dejá así, maunifik).
3. Para reseñas: Si el usuario quiere calificar, pide el negocio, la calificación (1-5) y opcionalmente un comentario.
4. Si preguntan por productos/precios específicos que no tienes, sugiere llamar al negocio.
5. Siempre que sea el primer mensaje, saluda: "Hola, soy Luisa el asistente de Parchaoo..."
6. Formatea los precios como: $50.000

**MENSAJE DEL USUARIO:** "{message}"

Responde de forma útil y completa usando TODA la información disponible arriba."""

            prompt = system_prompt.format(
                db_context=db_context if db_context else "No hay información específica disponible.",
                hora_actual=hora_actual,
                context=context if context else "Primera interacción",
                intencion=intencion,
                message=message
            )
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        
        except Exception as e:
            logger.error(f"Error en Gemini: {e}")
            return "¡Ey, manit@! Se me cruzaron los cables. ¿Me repites porfa?"
