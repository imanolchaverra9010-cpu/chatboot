"""
Servicio para interactuar con Google Gemini AI - ESPECIALIZADO EN NEGOCIOS
"""
import logging
import google.generativeai as genai
from django.conf import settings
from .db_service import DatabaseService
from datetime import datetime

logger = logging.getLogger('chatbot')


class GeminiService:
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.db_service = DatabaseService()
        
        if not self.api_key:
            logger.warning("API de Gemini sin configurar")
            return
        
        # Configurar Gemini
        genai.configure(api_key=self.api_key)
        
        # Configuración del modelo
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        
        # Configuración de seguridad
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        
        # Inicializar modelo con capacidades multimodales
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
    
    def _extraer_informacion_negocios(self, message):
        """
        Extraer información relevante de negocios según el mensaje
        
        Returns:
            String con contexto de negocios
        """
        context = ""
        message_lower = message.lower()
        
        try:
            # Palabras clave para búsqueda de negocios
            keywords_negocios = ['negocio', 'tienda', 'local', 'restaurante', 'farmacia', 
                                'panadería', 'supermercado', 'ferretería', 'dónde', 'donde',
                                'panaderia', 'ferreteria']
            
            keywords_horarios = ['horario', 'abierto', 'cerrado', 'abre', 'cierra', 'hora', 
                               'atiende', 'atención', 'atencion', 'funciona']
            
            keywords_ubicacion = ['ubicación', 'ubicacion', 'dirección', 'direccion', 'queda', 
                                'está', 'esta', 'como llego', 'donde queda', 'barrio', 'cerca']
            
            keywords_productos = ['producto', 'vende', 'venden', 'precio', 'cuánto cuesta', 
                                'cuanto cuesta', 'tiene', 'hay', 'servicio', 'venta']
            
            # Detectar categoría específica
            categorias_map = {
                'restaurante': ['restaurante', 'comida', 'comer', 'almuerzo', 'desayuno', 'comedor'],
                'farmacia': ['farmacia', 'droguería', 'drogueria', 'medicina', 'medicamento'],
                'supermercado': ['supermercado', 'mercado', 'tienda', 'viveres', 'víveres'],
                'panadería': ['panadería', 'panaderia', 'pan', 'pandería'],
                'ferretería': ['ferretería', 'ferreteria', 'herramienta', 'ferreteria'],
                'ropa': ['ropa', 'boutique', 'vestido', 'zapato', 'calzado'],
                'tecnología': ['celular', 'computador', 'tecnología', 'tecnologia', 'electrónica']
            }
            
            categoria_detectada = None
            for cat, keywords in categorias_map.items():
                if any(kw in message_lower for kw in keywords):
                    categoria_detectada = cat
                    break
            
            # Buscar negocios - SIEMPRE buscar si hay palabras clave o categoría
            negocios = None
            if any(kw in message_lower for kw in keywords_negocios) or categoria_detectada:
                negocios = self.db_service.buscar_negocios(
                    query=message if len(message.split()) < 10 else None,
                    categoria=categoria_detectada,
                    limit=5
                )
            # También buscar si pregunta por algo específico sin palabras clave obvias
            elif len(message.split()) <= 5 and len(message) > 3:
                negocios = self.db_service.buscar_negocios(
                    query=message,
                    limit=5
                )
            
            if negocios and len(negocios) > 0:
                context += "\n\n🏪 **NEGOCIOS QUE TE PUEDEN SERVIR:**\n"
                for neg in negocios:
                    verificado = "✅" if neg.verificado else ""
                    context += f"\n**{neg.nombre}** {verificado}\n"
                    context += f"📍 {neg.direccion}"
                    if neg.barrio:
                        context += f" - {neg.barrio}"
                    context += f"\n📞 {neg.telefono if neg.telefono else 'Sin teléfono'}\n"
                    
                    if neg.categoria:
                        context += f"🏷️ {neg.categoria}\n"
                    
                    # Verificar si está abierto
                    estado = self.db_service.verificar_negocio_abierto(neg.id)
                    if estado['abierto'] is not None:
                        emoji = "🟢" if estado['abierto'] else "🔴"
                        context += f"{emoji} {estado['mensaje']}\n"
            
            # Información de horarios
            if any(kw in message_lower for kw in keywords_horarios):
                # Buscar negocio mencionado
                palabras = message_lower.split()
                for palabra in palabras:
                    if len(palabra) > 4:
                        negocios = self.db_service.buscar_negocios(query=palabra, limit=3)
                        if negocios:
                            for negocio in negocios:
                                horarios = self.db_service.obtener_horarios_negocio(negocio.id)
                                if horarios:
                                    context += f"\n\n🕐 **HORARIOS DE {negocio.nombre.upper()}:**\n"
                                    for h in horarios:
                                        if h.cerrado:
                                            context += f"• {h.dia_semana.capitalize()}: Cerrado\n"
                                        else:
                                            context += f"• {h.dia_semana.capitalize()}: {h.hora_apertura.strftime('%I:%M %p')} - {h.hora_cierre.strftime('%I:%M %p')}\n"
                                            if h.notas:
                                                context += f"  ℹ️ {h.notas}\n"
                                    
                                    # Estado actual
                                    estado = self.db_service.verificar_negocio_abierto(negocio.id)
                                    emoji = "🟢" if estado['abierto'] else "🔴"
                                    context += f"\n{emoji} Ahora: {estado['mensaje']}\n"
                            break
            
            # Información de ubicación
            if any(kw in message_lower for kw in keywords_ubicacion):
                palabras = message_lower.split()
                for palabra in palabras:
                    if len(palabra) > 4:
                        negocios = self.db_service.buscar_negocios(query=palabra, limit=2)
                        if negocios:
                            context += "\n\n📍 **UBICACIONES:**\n"
                            for neg in negocios:
                                context += f"\n**{neg.nombre}**\n"
                                context += f"• Dirección: {neg.direccion}\n"
                                if neg.barrio:
                                    context += f"• Barrio: {neg.barrio}\n"
                                if neg.referencia_ubicacion:
                                    context += f"• Referencia: {neg.referencia_ubicacion}\n"
                                if neg.telefono:
                                    context += f"• Teléfono: {neg.telefono}\n"
                                # Agregar coordenadas si están disponibles
                                if neg.latitud and neg.longitud:
                                    context += f"• Coordenadas: {neg.latitud}, {neg.longitud}\n"
                                    context += f"📌 [Puedo enviarte la ubicación exacta si lo deseas]\n"
                            break
            
            # Información de productos/servicios
            if any(kw in message_lower for kw in keywords_productos):
                # Buscar primero el negocio
                palabras = message_lower.split()
                for palabra in palabras:
                    if len(palabra) > 4:
                        negocios = self.db_service.buscar_negocios(query=palabra, limit=2)
                        if negocios:
                            for negocio in negocios:
                                productos = self.db_service.obtener_productos_negocio(negocio.id, limit=8)
                                if productos:
                                    context += f"\n\n🛍️ **PRODUCTOS/SERVICIOS DE {negocio.nombre.upper()}:**\n"
                                    for p in productos:
                                        destacado = "⭐" if p.destacado else "•"
                                        context += f"{destacado} {p.nombre} - {p.get_precio_display()}\n"
                                        if p.descripcion:
                                            context += f"  {p.descripcion[:80]}...\n"
                            break
            
            # Categorías disponibles
            if 'categoría' in message_lower or 'categoria' in message_lower or 'tipos de negocio' in message_lower:
                categorias = self.db_service.obtener_categorias_negocios()
                if categorias:
                    context += "\n\n🏷️ **CATEGORÍAS DISPONIBLES:**\n"
                    if isinstance(categorias[0], str):
                        context += ", ".join(categorias)
                    else:
                        for cat in categorias:
                            emoji = cat.icono if hasattr(cat, 'icono') and cat.icono else "•"
                            context += f"{emoji} {cat.nombre}\n"
            
            # Búsqueda por barrio
            for palabra in message_lower.split():
                if len(palabra) > 4:
                    negocios_barrio = self.db_service.buscar_negocios_cercanos(barrio=palabra, limit=3)
                    if negocios_barrio:
                        context += f"\n\n🗺️ **NEGOCIOS EN {palabra.upper()}:**\n"
                        for neg in negocios_barrio:
                            context += f"• {neg.nombre} - {neg.direccion}\n"
                        break
        
        except Exception as e:
            logger.error(f"Error extrayendo información de negocios: {e}")
        
        return context
    
    def get_response(self, message, context=None, phone_number=None):
        """
        Generar respuesta usando Gemini con contexto de negocios
        
        Args:
            message: Mensaje del usuario
            context: Contexto de conversación previo
            phone_number: Número de teléfono del usuario
        
        Returns:
            Respuesta generada por Gemini
        """
        if not self.api_key:
            return "Lo siento, el servicio de IA no está configurado correctamente."
        
        try:
            # Extraer información de la base de datos de negocios
            db_context = self._extraer_informacion_negocios(message)
            
            # Información adicional
            hora_actual = datetime.now().strftime("%I:%M %p")
            dia_actual = datetime.now().strftime("%A")
            dias_es = {
                'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miércoles',
                'Thursday': 'jueves', 'Friday': 'viernes', 'Saturday': 'sábado', 'Sunday': 'domingo'
            }
            dia_actual = dias_es.get(dia_actual, dia_actual)
            
            # Construir prompt con contexto - LENGUAJE NATIVO DE QUIBDÓ
            system_prompt = """Eres Luisa, una paisana de Quibdó que ayuda a la gente a encontrar negocios y servicios por aquí.

**CÓMO ERES:**
- Hablas como la gente de Quibdó, natural y chevere
- Usas expresiones locales: "mi amor", "mi reina", "mijo/mija", "ve pues", "ombe", "qué más", "bacano", "chévere"
- Eres cálida, amable y servicial como la gente del Chocó
- Ayudas con toda la buena energía 😊
- Hablas claro y directo, sin tanta vuelta

**TU FORMA DE HABLAR:**
- "Mirá mi amor, te cuento..."
- "Ombe sí, hay varios lugares..."
- "Ve pues, ese negocio queda por..."
- "Ay mija/mijo, déjame ver..."
- "Qué más, ¿en qué te ayudo?"
- "Bacano, te paso la info..."
- "Uy no mi reina, ese lugar está cerrado ahora"
- "Claro que sí, con mucho gusto"

**INFORMACIÓN DE HOY:**
📅 Hoy es {dia_actual}
🕐 Son las {hora_actual}

**INFO DE LOS NEGOCIOS:**
{db_context}

**LO QUE HABLAMOS ANTES:**
{context}

**EL USUARIO DICE:**
{message}

**IMPORTANTE:**
1. Usa SIEMPRE la información de los negocios que te di arriba
2. Si hay negocios en la lista, menciónalos con sus datos completos
3. Habla como paisana de Quibdó, natural y chevere
4. Usa expresiones locales pero sin exagerar
5. Sé específica con direcciones y horarios
6. Precios en formato colombiano: $50.000
7. Respuestas cortas y claras (2-3 párrafos máximo)
8. Si no sabes algo, dilo honesto y ofrece ayuda

**RESPONDE COMO PAISANA DE QUIBDÓ:**"""
            
            prompt = system_prompt.format(
                dia_actual=dia_actual,
                hora_actual=hora_actual,
                db_context=db_context if db_context else "No hay información específica de la base de datos para esta consulta.",
                context=context if context else "No hay conversación previa",
                message=message
            )
            
            # Generar respuesta
            response = self.model.generate_content(prompt)
            
            if response.text:
                logger.info(f"Respuesta de Gemini generada con contexto de negocios")
                return response.text.strip()
            else:
                logger.warning("Gemini no generó respuesta de texto")
                return "Lo siento, no pude generar una respuesta en este momento."
        
        except Exception as e:
            logger.error(f"Error generando respuesta con Gemini: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error al procesar tu mensaje. Por favor intenta de nuevo."
    
    def get_response_with_history(self, messages_history, phone_number=None):
        """
        Generar respuesta usando historial completo
        
        Args:
            messages_history: Lista de diccionarios con 'role' y 'content'
            phone_number: Número de teléfono del usuario
        
        Returns:
            Respuesta generada por Gemini
        """
        if not self.api_key:
            return "Lo siento, el servicio de IA no está configurado correctamente."
        
        try:
            # Obtener último mensaje para contexto DB
            last_message = messages_history[-1]['content'] if messages_history else ""
            db_context = self._extraer_informacion_negocios(last_message)
            
            # Iniciar chat
            chat = self.model.start_chat(history=[])
            
            # Agregar contexto de base de datos al primer mensaje
            if db_context and messages_history:
                first_msg = f"{db_context}\n\n{messages_history[0]['content']}"
                messages_history[0]['content'] = first_msg
            
            # Procesar historial
            for msg in messages_history[:-1]:
                if msg['role'] == 'user':
                    chat.send_message(msg['content'])
            
            # Enviar último mensaje
            response = chat.send_message(last_message)
            
            if response.text:
                return response.text.strip()
            else:
                return "Lo siento, no pude generar una respuesta."
        
        except Exception as e:
            logger.error(f"Error con historial de Gemini: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error al procesar tu mensaje."
    
    def analyze_image(self, image_path, user_message="", context=""):
        """
        Analizar imagen usando Gemini Vision
        
        Args:
            image_path: Ruta local de la imagen
            user_message: Mensaje del usuario (opcional)
            context: Contexto adicional
        
        Returns:
            Análisis de la imagen
        """
        if not self.api_key:
            return "Lo siento, el servicio de análisis de imágenes no está configurado."
        
        try:
            from PIL import Image
            
            # Cargar imagen
            img = Image.open(image_path)
            
            # Construir prompt
            prompt = f"""Ey mi amor, soy Luisa, una paisana de Quibdó que te ayuda con lo que necesites.

Mirá, voy a ver esta imagen que me mandaste y te cuento qué veo:

**Si es un menú de restaurante:** Te digo qué platos hay, los precios y todo eso
**Si es un producto:** Te describo qué es y lo que se ve
**Si es una ubicación o negocio:** Te cuento qué veo ahí
**Si es otra cosa:** Te explico lo que hay

**Lo que me dijiste:** {user_message if user_message else "¿Qué ves en esta imagen?"}

**Contexto:** {context if context else "Sin contexto adicional"}

Ombe, te respondo clarito y con buena onda 😊 Hablo como la gente de por acá, natural y chevere."""
            
            # Generar respuesta con imagen
            response = self.model.generate_content([prompt, img])
            
            if response.text:
                logger.info("Imagen analizada exitosamente con Gemini Vision")
                return response.text.strip()
            else:
                return "No pude analizar la imagen en este momento."
        
        except Exception as e:
            logger.error(f"Error analizando imagen: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error al analizar la imagen. Por favor intenta de nuevo."
    
    def transcribe_audio(self, audio_path):
        """
        Transcribir audio a texto
        
        Args:
            audio_path: Ruta local del archivo de audio
        
        Returns:
            Texto transcrito
        """
        if not self.api_key:
            return None
        
        try:
            # Gemini 2.0 puede procesar audio directamente
            import mimetypes
            
            # Detectar tipo de archivo
            mime_type, _ = mimetypes.guess_type(audio_path)
            
            # Subir archivo a Gemini
            audio_file = genai.upload_file(path=audio_path)
            
            # Crear prompt para transcripción
            prompt = """Transcribe el siguiente audio a texto en español.
            
Proporciona SOLO la transcripción exacta, sin comentarios adicionales."""
            
            # Generar transcripción
            response = self.model.generate_content([prompt, audio_file])
            
            if response.text:
                logger.info("Audio transcrito exitosamente")
                return response.text.strip()
            else:
                logger.warning("No se pudo transcribir el audio")
                return None
        
        except Exception as e:
            logger.error(f"Error transcribiendo audio: {str(e)}", exc_info=True)
            return None
    
    def analyze_sentiment(self, text):
        """Analizar sentimiento de un texto"""
        if not self.api_key:
            return {'sentiment': 'neutral', 'score': 0.5}
        
        try:
            prompt = f"""Analiza el sentimiento del siguiente texto y responde SOLO con una palabra:
'positivo', 'negativo' o 'neutral'

Texto: {text}

Sentimiento:"""
            
            response = self.model.generate_content(prompt)
            sentiment_text = response.text.strip().lower()
            
            sentiment_map = {
                'positivo': 'positive',
                'negativo': 'negative',
                'neutral': 'neutral'
            }
            
            sentiment = sentiment_map.get(sentiment_text, 'neutral')
            
            return {'sentiment': sentiment, 'score': 0.5}
        
        except Exception as e:
            logger.error(f"Error analizando sentimiento: {e}")
            return {'sentiment': 'neutral', 'score': 0.5}
