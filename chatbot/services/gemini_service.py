"""
Servicio para interactuar con Google Gemini AI - ESPECIALIZADO EN NEGOCIOS
"""
import logging
import time
import google.generativeai as genai
from django.conf import settings
from .db_service import DatabaseService
from datetime import datetime

try:
    from google.api_core.exceptions import ResourceExhausted
except ImportError:
    ResourceExhausted = Exception  # fallback si no está disponible

logger = logging.getLogger('chatbot')

# Mensaje amigable cuando se excede la cuota de Gemini (free tier ~20 req/día)
MSG_CUOTA_EXCEDIDA = (
    "Ey manito, por ahora alcanzamos el límite de consultas del día. "
    "Escribe *HUMANO* para hablar con un asesor, o intenta mañana."
)


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
        
        # Modelo configurable (free tier: gemini-2.5-flash ~20 req/día)
        self.model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')
        self.fallback_model = getattr(settings, 'GEMINI_FALLBACK_MODEL', 'gemini-1.5-flash')
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
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
            # Palabras clave para búsqueda de negocios (incluye lista, restaurantes, farmacias, etc.)
            keywords_negocios = ['negocio', 'negocios', 'tienda', 'tiendas', 'local', 'locales',
                                'restaurante', 'restaurantes', 'farmacia', 'farmacias',
                                'panadería', 'panaderias', 'panaderías', 'supermercado', 'supermercados',
                                'ferretería', 'ferreterias', 'ferreterías', 'drogueria', 'droguería',
                                'dónde', 'donde', 'lista', 'listado', 'cuáles', 'cuales',
                                'qué hay', 'que hay', 'dame', 'busco', 'necesito', 'conoces']
            
            keywords_horarios = ['horario', 'abierto', 'cerrado', 'abre', 'cierra', 'hora', 
                               'atiende', 'atención', 'atencion', 'funciona']
            
            keywords_ubicacion = ['ubicación', 'ubicacion', 'dirección', 'direccion', 'queda', 
                                'está', 'esta', 'como llego', 'donde queda', 'barrio', 'cerca']
            
            keywords_productos = ['producto', 'vende', 'venden', 'precio', 'cuánto cuesta', 
                                'cuanto cuesta', 'tiene', 'hay', 'servicio', 'venta']
            
            # NUEVO: Palabras clave para reseñas
            keywords_resenas = ['reseña', 'resena', 'calificar', 'calificación', 'calificacion',
                               'opinión', 'opinion', 'comentario', 'valorar', 'valoración',
                               'estrellas', 'review']
            
            # NUEVO: Palabras clave para eventos deportivos
            keywords_eventos = ['evento', 'partido', 'juego', 'campeonato', 'torneo',
                               'futbol', 'fútbol', 'baloncesto', 'basquet', 'voleibol',
                               'deporte', 'deportivo', 'estadio', 'cancha']
            
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
                # Si pide lista por categoría (restaurantes, farmacias), buscar SOLO por categoría
                # No pasar el mensaje completo como query o filtrará mal
                query_busqueda = None
                if categoria_detectada:
                    query_busqueda = None  # Solo categoría
                else:
                    # Extraer término de búsqueda si es corto (ej: "panaderia centro")
                    palabras = [p for p in message_lower.split() if len(p) > 3 and p not in keywords_negocios]
                    if len(palabras) <= 3 and palabras:
                        query_busqueda = palabras[0] if len(palabras[0]) > 4 else None
                negocios = self.db_service.buscar_negocios(
                    query=query_busqueda,
                    categoria=categoria_detectada,
                    limit=10
                )
            # También buscar si pregunta por algo específico sin palabras clave obvias
            elif len(message.split()) <= 5 and len(message) > 3:
                negocios = self.db_service.buscar_negocios(
                    query=message,
                    limit=10
                )
            
            # Mensaje explícito si pidieron lista pero no hay resultados
            pidio_lista = any(kw in message_lower for kw in ['lista', 'listado', 'restaurantes', 'farmacias', 'negocios', 'cuáles', 'cuales', 'qué hay', 'que hay'])
            if pidio_lista and (not negocios or len(negocios) == 0):
                context += "\n\n🏪 **NEGOCIOS:** No hay negocios registrados en esa categoría. El usuario pidió lista de restaurantes/farmacias/etc. Responde que por ahora no tenemos esa información cargada en el sistema.\n"
            
            if negocios and len(negocios) > 0:
                context += "\n\n🏪 **NEGOCIOS QUE TE PUEDEN SERVIR, PARCE:**\n"
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
                    
                    # NUEVO: Agregar productos/menú automáticamente
                    productos = self.db_service.obtener_productos_negocio(neg.id, limit=5)
                    if productos and len(productos) > 0:
                        context += f"\n🍽️ **Menú/Productos:**\n"
                        for p in productos[:5]:  # Máximo 5 productos
                            destacado = "⭐" if p.destacado else "•"
                            context += f"  {destacado} {p.nombre} - {p.get_precio_display()}\n"
                            if p.descripcion and len(p.descripcion) > 0:
                                desc_corta = p.descripcion[:60] + "..." if len(p.descripcion) > 60 else p.descripcion
                                context += f"    ({desc_corta})\n"
                    context += "\n"  # Espacio entre negocios
            
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
            
            # NUEVO: Información de eventos deportivos
            if any(kw in message_lower for kw in keywords_eventos):
                eventos = self.db_service.obtener_eventos_proximos(dias=14, limit=5)
                if eventos:
                    context += "\n\n⚽ **EVENTOS DEPORTIVOS PRÓXIMOS:**\n"
                    for evento in eventos:
                        context += f"\n**{evento.nombre}**\n"
                        if evento.equipo_local and evento.equipo_visitante:
                            context += f"🏆 {evento.equipo_local} vs {evento.equipo_visitante}\n"
                        context += f"📅 {evento.fecha_evento.strftime('%A %d de %B, %I:%M %p')}\n"
                        context += f"📍 {evento.lugar}"
                        if evento.barrio:
                            context += f" - {evento.barrio}"
                        context += "\n"
                        if evento.entrada_gratis:
                            context += "💰 Entrada GRATIS\n"
                        elif evento.precio_entrada:
                            context += f"💰 Entrada: ${evento.precio_entrada:,.0f}\n"
                        if evento.descripcion:
                            desc_corta = evento.descripcion[:100] + "..." if len(evento.descripcion) > 100 else evento.descripcion
                            context += f"ℹ️ {desc_corta}\n"
            
            # NUEVO: Información sobre reseñas
            if any(kw in message_lower for kw in keywords_resenas):
                context += "\n\n⭐ **SOBRE RESEÑAS:**\n"
                context += "Puedes dejar tu reseña de un negocio diciendo:\n"
                context += "• 'Quiero calificar [nombre del negocio]'\n"
                context += "• 'Dejar reseña de [nombre del negocio]'\n"
                context += "Te pediré tu calificación (1-5 estrellas) y tu comentario.\n"
            
            # === MÓDULO BOLETERÍA (precios, puntos de venta, links) ===
            keywords_boleteria = ['boletería', 'boleteria', 'boleto', 'entrada', 'comprar entrada',
                                 'precio entrada', 'puntos de venta', 'link compra', 'ticket']
            if any(kw in message_lower for kw in keywords_boleteria + keywords_eventos):
                eventos_list = self.db_service.obtener_eventos_proximos(dias=30, limit=5)
                boleteria_agregada = False
                for evento in eventos_list:
                    boleto = self.db_service.obtener_boleteria_evento(evento_id=evento.id)
                    if boleto:
                        boleteria_agregada = True
                        context += f"\n\n🎫 **BOLETERÍA - {evento.nombre}:**\n"
                        if boleto.entrada_gratis:
                            context += "💰 Entrada GRATIS\n"
                        else:
                            if boleto.precio_general:
                                context += f"💰 General: ${boleto.precio_general:,.0f}\n"
                            if boleto.precio_vip:
                                context += f"💰 VIP: ${boleto.precio_vip:,.0f}\n"
                            if boleto.precio_niños:
                                context += f"💰 Niños: ${boleto.precio_niños:,.0f}\n"
                        if boleto.puntos_venta:
                            context += f"📍 Puntos de venta: {boleto.puntos_venta}\n"
                        if boleto.link_compra:
                            context += f"🔗 Comprar en línea: {boleto.link_compra}\n"
                if not boleteria_agregada and eventos_list:
                    context += "\n\n🎫 **BOLETERÍA:** Consulta la agenda de eventos. Los precios se publican por evento.\n"
            
            # === MÓDULO TRÁMITES Y REQUISITOS ===
            keywords_tramites = ['trámite', 'tramite', 'requisitos', 'requisito', 'documentos',
                                'cita', 'certificado', 'licencia', 'permiso', 'turno', 'sacar']
            if any(kw in message_lower for kw in keywords_tramites):
                tramites = self.db_service.obtener_tramites(query=message, limit=5)
                if tramites:
                    context += "\n\n📋 **TRÁMITES Y REQUISITOS:**\n"
                    for t in tramites:
                        context += f"\n**{t.nombre}**\n"
                        context += f"📝 {t.descripcion[:150]}...\n" if len(t.descripcion) > 150 else f"📝 {t.descripcion}\n"
                        if t.entidad:
                            context += f"🏛️ Entidad: {t.entidad}\n"
                        if t.requisitos:
                            reqs = t.requisitos if isinstance(t.requisitos, list) else []
                            for r in reqs[:5]:
                                context += f"  • {r}\n"
                        if t.costo:
                            context += f"💰 Costo: ${t.costo:,.0f}\n"
                        if t.link_turno:
                            context += f"🔗 Sacar turno: {t.link_turno}\n"
                        if t.horario_atencion:
                            context += f"🕐 {t.horario_atencion}\n"
            
            # === MÓDULO TURNOS (reservar/cancelar) ===
            keywords_turnos = ['turno disponible', 'reservar turno', 'cancelar turno', 'turnos',
                              'agendar', 'reservar cita', 'cancelar cita', 'citas disponibles']
            if any(kw in message_lower for kw in keywords_turnos):
                turnos = self.db_service.obtener_turnos_disponibles(limit=10)
                if turnos:
                    context += "\n\n📅 **TURNOS DISPONIBLES:**\n"
                    context += "Puedes decir 'reservar turno [número]' o 'cancelar turno [número]'\n"
                    for i, t in enumerate(turnos[:8], 1):
                        context += f"{i}. {t.servicio} - {t.fecha_turno} {t.hora_inicio.strftime('%H:%M')} (ID: {t.id})\n"
                if phone_number:
                    mis_turnos = self.db_service.obtener_turnos_usuario(phone_number)
                    if mis_turnos:
                        context += "\n📌 **TUS TURNOS RESERVADOS:**\n"
                        for t in mis_turnos:
                            context += f"• {t.servicio} - {t.fecha_turno} {t.hora_inicio.strftime('%H:%M')} (ID: {t.id})\n"
            
            # === MÓDULO CÓMO LLEGAR (mapas, rutas, transporte) ===
            keywords_como_llegar = ['cómo llegar', 'como llegar', 'ruta', 'transporte', 'mapa',
                                   'direcciones', 'ubicación', 'ubicacion', 'waze', 'google maps']
            if any(kw in message_lower for kw in keywords_como_llegar):
                palabras = message_lower.split()
                for palabra in palabras:
                    if len(palabra) > 4:
                        negocios = self.db_service.buscar_negocios(query=palabra, limit=3)
                        if negocios:
                            context += "\n\n🗺️ **CÓMO LLEGAR:**\n"
                            for neg in negocios:
                                link = self.db_service.generar_link_google_maps(
                                    neg.direccion, neg.latitud, neg.longitud
                                )
                                if link:
                                    context += f"**{neg.nombre}:** {link}\n"
                            break
                        eventos = self.db_service.buscar_eventos(query=palabra)
                        if eventos:
                            context += "\n\n🗺️ **CÓMO LLEGAR AL EVENTO:**\n"
                            for ev in eventos[:2]:
                                link = self.db_service.generar_link_google_maps(
                                    f"{ev.lugar} {ev.direccion or ''}"
                                )
                                if link:
                                    context += f"**{ev.nombre} - {ev.lugar}:** {link}\n"
                            break
            
            # === MÓDULO ALERTAS (cambios de última hora) - SIEMPRE incluir ===
            try:
                alertas = self.db_service.obtener_alertas_activas(limit=5)
            except Exception:
                alertas = []
            if alertas:
                context += "\n\n⚠️ **ALERTAS Y CAMBIOS DE ÚLTIMA HORA:**\n"
                for a in alertas:
                    context += f"• [{a.tipo.upper()}] {a.titulo}: {a.mensaje}\n"
        
        except Exception as e:
            logger.error(f"Error extrayendo información de negocios: {e}")
        
        return context
    
    def _generate_with_retry(self, prompt, max_retries=1, retry_delay=50):
        """
        Llama a generate_content con reintento ante error 429 (cuota/rate limit).
        Retorna None si se excedió la cuota tras los reintentos.
        """
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                return self.model.generate_content(prompt)
            except Exception as e:
                is_429 = isinstance(e, ResourceExhausted) or getattr(e, 'code', None) == 429
                if not is_429:
                    raise
                if attempt < max_retries:
                    logger.warning(f"Gemini 429, reintentando en {retry_delay}s (intento {attempt + 1}/{max_retries + 1})")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Gemini: cuota excedida tras {max_retries + 1} intentos: {e}")
                    return None
        return None
    
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
            
            # Construir prompt con contexto - LENGUAJE BARRIAL DE QUIBDÓ
            system_prompt = """Eres Luisa, una parcera de barrio de Quibdó que ayuda a la gente a encontrar negocios y servicios.

**CÓMO HABLAS:**
- Hablas bien barrial, como la gente del barrio en Quibdó
- Usas: "parce", "manito/manita"
- También: "ombe", "ve pues", "mirá", "qué más", "bacano", "chévere", "de una"
- Eres cálida y servicial, pero bien callejera en el buen sentido
- Hablas claro y directo, sin rodeos

**EJEMPLOS DE CÓMO HABLAS:**
- "manito, ¿en qué te ayudo?"
- "Ey manito, mirá estos lugares..."
- "Ve manito, ese negocio queda por..."
- "mano, déjame yo veo..."
- "ey manito, yaa te ayudo con ese dato..."
- "vee mano, ese negocio está cerrado"
- "Dale mano, con mucho gusto"
- "Eppa manito, ya te ayudo con eso..."
- "te comento mi hermano..."

**INFORMACIÓN DE HOY:**
📅 Hoy es {dia_actual}
🕐 Son las {hora_actual}

**INFO DE LOS NEGOCIOS:**
{db_context}

**LO QUE HABLAMOS ANTES:**
{context}

**EL USUARIO DICE:**
{message}

**MÓDULOS QUE PUEDES ATENDER:**
• Informativo: ubicación de locales, horarios, agenda eventos, boletería, requisitos de trámites
• Logístico: turnos (reservar/cancelar), cómo llegar (mapas/rutas), alertas de cambios
• Si NO puedes resolver: di "Escribe *HUMANO* para hablar con un asesor" (esto escala a humano)

**IMPORTANTE:**
1. USA SIEMPRE la información que te di arriba (negocios, eventos, boletería, trámites, turnos, alertas)
2. Si hay negocios en la INFO DE NEGOCIOS, SIEMPRE enumera la lista completa. NUNCA digas que no hay cuando la lista está arriba
3. Si hay negocios, menciónalos CON SUS PRODUCTOS/MENÚS incluidos
3. Habla bien barrial pero respetuoso, como parcero de barrio
4. Usa "parce", "manito", "llave", "hermano" - varía las expresiones
5. Sé específica con direcciones, horarios, precios y LINKS cuando existan
6. Precios en formato colombiano: $50.000
7. Respuestas cortas y directas (2-3 párrafos máximo)
8. Si NO sabes algo o NO puedes resolver: di honesto "Escribe *HUMANO* para hablar con un asesor"
9. Si hay eventos deportivos en la info, menciónalos con boletería y links de compra si aplica
10. Si preguntan por reseñas, explica cómo dejar una calificación

**James**

cuando te pregunten por James Mosquera (el bacachico)
ten encuenta la siguiente informacion y da respuestas muy formales:

QUE HEMOS REALIZADO DURANTE 3 AÑOS DEL CONGRESO:
3 años de trabajo legislativo con 110 proyectos como autor/coautor, 45 como ponente, 30 debates de control político:
•	Ley de víctimas
•	Ministerio de Igualdad
•	Reforma Agraria
•	Reforma a la Justicia
•	Prórroga municipios PDET
•	Senado Afro
•	Min Igualdad
•	Campesino como sujeto de derecho
•	Reforma a la educación
•	Ponente de la Reforma a la educación como derecho
•	fundamental.
•	Canales universitarios y acceso para jóvenes afro.
•	Autor del Proyecto de Ley Atención móvil e itinerante en salud en zonas de difícil acceso geográfico.
HEMOS PARTICIPADO EN 30 DEBATES DE CONTROL POLÍTICO COMO: 
•	Comisionado de Paz
•	Sector Transporte
•	Sector educación
•	Sector Salud
•	Sector Agricultura
PERTENEZCO A LAS SIGUIENTES COMISIONES DEL CONGRESO DE LA REPÚBLICA: 
•	Comisión Primera Constitucional Permanente
•	Comisión Legal de Cuentas – presidente 2024-2025.
•	Comisión Legal de Paz y Posconflicto- presidente durante 2023- 2025
•	Comisión Legal Afrocolombiana
•	Comisión Infancia y Adolescencia
•	Comisión Accidental Seguimiento y control en materia minero- energética
•	Comisión Accidental de seguimiento a los programas de desarrollo con enfoque territorial 
•	PDET
•	Comisión Accidental de seguimiento a la implementación del acuerdo de paz entre el
•	estado colombiano y las FARC EP.
•	Comisión Accidental de agua y biodiversidad.
•	Comisión Accidental anticorrupción y de integridad pública.
•	Comisión accidental de seguimiento a las políticas en materia de diversidad biológica y
•	su cumplimiento en Colombia – COP16.
QUE HEMOS REALIZADO DURANTE EL JULIO A NOVIEMBRE DE 2026
•	Se encuentra para último debate el proyecto de ley que prórroga por 10 años más la vigencia de los PDET
•	Se aprobó en primer debate el proyecto de ley que protege al pez bocachico.
•	Se encuentra para tercer debate el proyecto de ley que busca mayor apoyo a las fiestas de San pacho.
•	Soy ponente del proyecto de ley de paz total.
•	Durante esta legislatura: Hemos participado de debate de control político a las entidades encargadas del cumplimiento del acuerdo de paz. 
•	El 10 octubre realizamos una audiencia pública en Nuevo Belén de Bajirá 
•	EL 31 de julio realizamos audiencia pública en Quibdó en compañía de la comisión de paz. 
•	Soy ponente del proyecto de ley de despenalizada a los pequeños cultivadores, nos encotramos pendiente de realizar audiencia pública. 



QUE RETOS TENEMOS POR CUMPLIR:
¿Por qué queremos volver?
•	Es necesario lograr una ley que le de beneficios tributarios al departamento del chocó, como lo fue la Ley paez. 
•	Queremos reconocer Acandí como un lugar de turismo.
•	Impulsar la creación de la Curul Afrocolombiana en el Senado de la República, como mecanismo de representación política efectiva para las comunidades afrodescendientes.
•	Promover una ley para la protección y conservación del pez Bocachico, garantizando
•	su sostenibilidad ecológica y el sustento de las comunidades ribereñas que dependen de esta
•	especie.
•	Seguir exigiéndole al Gobierno Nacional, que la inversión social llegue a todos los municipios, y lograr construir una paz territorial real y duradera.
•	Queremos que se convierta en ley nuestro proyecto de turismo comunitario que le aporta grandes beneficios a nuestras comunidades.
No vengo a improvisar. Vengo a completar la tarea que el territorio me encomendó.

Usted tiene una demanda en la Corte
He actuado siempre dentro de la ley y de buena fe. Es un proceso que está en manos de la justicia, lo asumo con tranquilidad y respeto. No me distrae, porque mi prioridad sigue siendo el territorio.
Del total nacional de víctimas: 10.140.985 de las cuales 689.013 son del Departamento del Chocó. Es decir, las víctimas del Chocó representan aproximadamente el 6,79% del total nacional registrado de víctimas del conflicto armado.
De cada 100 víctimas del conflicto armado en Colombia, casi 7 son del Chocó.Esto muestra que el departamento, pese a tener una baja participación poblacional a nivel nacional, tiene una altísima carga de victimización. No queda duda, que en el departamento todos somos víctimas. 
No estoy improvisando. Tengo resultados concretos, experiencia legislativa, gestión en territorio e independencia de maquinarias. Y algo más importante: tengo una historia de vida ligada al Chocó y a la gente que represento.






LOGROS: 
•	Aprobamos la Ley, que permite el aumento de honorarios en 39.56%, más sesiones y cobertura en seguridad social, de los concejales.
•	Capacitación con CONFENACOL a concejales de Medio Atrato
•	Se gestionó con la Embajada de EE. UU. la priorización de becas para cursos de Policía con el programa 'Vamos Sumando.
•	Apertura de vuelos Satena en ruta Atrato Condoto–Pizarro
•	Encuentros con Monseñor Rueda y la vicepresidenta Francia Márquez.
•	Impulso a ferias e iniciativas productivas locales
•	Participación en el Pacto por el Chocó 14 municipios.
•	Apoyo a iniciativas del OCAD Paz y Regalías Étnicas.
•	el Ministerio de la Igualdad. 
Hemos trabajado directamente en territorio.
No desde un escritorio en Bogotá.
•	Logramos que iniciara la construcción del hospital de mediana complejidad de Istmina; gestionamos dotaciones para centros de salud, ambulancias, instituciones educativas, canchas deportivas. 
•	Movimos la apertura de rutas aéreas Satena,
•	Impulsamos vías como Belén de Bajirá–Riosucio y Nóvita–Sipí–Cartago, y estamos encima de las rutas Quibdó–Medellín y Quibdó–Pereira.
Acompañamos a Consejos Comunitarios y resguardos indígenas para que accedieran a regalías y programas del Estado.
•	Tercero, en la ola invernal actuamos de inmediato: gestionamos ayudas alimentarias con el ICBF para Istmina, Litoral del San Juan y Condoto; trasladamos solicitudes al Gobierno para maquinaria y atención; y citamos a las entidades responsables para exigir prevención y no solo reacción.
•	También hemos tenido una agenda internacional fuerte, llevando la voz del Chocó a Estados Unidos y logrando becas con la Embajada para jóvenes afrocolombianos.
Todo esto lo hemos hecho manteniendo una campaña limpia, sin ataques personales, sin maquinarias políticas.
Siempre he dicho: aquí no se trata de pelear, sino de trabajar.


**RESPONDE COMO PARCERA DE BARRIO:**"""
            
            prompt = system_prompt.format(
                dia_actual=dia_actual,
                hora_actual=hora_actual,
                db_context=db_context if db_context else "No hay información específica de la base de datos para esta consulta.",
                context=context if context else "No hay conversación previa",
                message=message
            )
            
            # Generar respuesta con retry en caso de 429 (cuota/rate limit)
            response = self._generate_with_retry(prompt)
            
            if response and response.text:
                logger.info(f"Respuesta de Gemini generada con contexto de negocios")
                return response.text.strip()
            elif response is None:
                return MSG_CUOTA_EXCEDIDA
            else:
                logger.warning("Gemini no generó respuesta de texto")
                return "Lo siento, no pude generar una respuesta en este momento."
        
        except ResourceExhausted:
            logger.warning("Gemini: cuota excedida (ResourceExhausted)")
            return MSG_CUOTA_EXCEDIDA
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
            try:
                response = chat.send_message(last_message)
            except ResourceExhausted:
                logger.warning("Gemini: cuota excedida en get_response_with_history")
                return MSG_CUOTA_EXCEDIDA
            
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
            prompt = f"""Ey parce, soy Luisa, tu parcera de barrio en Quibdó que te ayuda con lo que necesites.

Mirá manito, voy a ver esta imagen que me mandaste y te cuento qué veo:

**Si es un menú de restaurante:** Te digo qué platos hay, los precios y todo eso llave
**Si es un producto:** Te describo qué es y lo que se ve hermano
**Si es una ubicación o negocio:** Te cuento qué veo ahí parce
**Si es otra cosa:** Te explico lo que hay

**Lo que me dijiste:** {user_message if user_message else "¿Qué ves en esta imagen?"}

**Contexto:** {context if context else "Sin contexto adicional"}

Ombe, te respondo clarito y con buena onda 😊 Hablo como la gente de barrio, natural y chevere."""
            
            # Generar respuesta con imagen
            try:
                response = self.model.generate_content([prompt, img])
            except ResourceExhausted:
                logger.warning("Gemini: cuota excedida en analyze_image")
                return MSG_CUOTA_EXCEDIDA
            
            if response.text:
                logger.info("Imagen analizada exitosamente con Gemini Vision")
                return response.text.strip()
            else:
                return "No pude analizar la imagen en este momento."
        
        except Exception as e:
            logger.error(f"Error analizando imagen: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error al analizar la imagen. Por favor intenta de nuevo."
    
    def process_video(self, video_path, user_message="", context=""):
        """
        Procesar video usando Gemini (descripción, transcripción si tiene audio)
        
        Args:
            video_path: Ruta local del archivo de video
            user_message: Mensaje/pregunta del usuario (opcional)
            context: Contexto adicional
        
        Returns:
            Respuesta generada sobre el video
        """
        if not self.api_key:
            return "Lo siento, el servicio de análisis de videos no está configurado."
        
        try:
            video_file = genai.upload_file(path=video_path)
            
            prompt = f"""Ey parce, soy Luisa, tu parcera de barrio en Quibdó.

Mirá manito, voy a ver este video que me mandaste y te cuento qué pasa:

**Si es un video de un lugar/negocio:** Describo qué veo, dónde parece estar, qué hay
**Si tiene texto o menú:** Leo y resumo lo que dice
**Si es un evento o algo en vivo:** Cuento qué está pasando
**Si es otra cosa:** Te explico lo que veo y escucho

**Lo que me dijiste:** {user_message if user_message else "¿Qué ves en este video?"}

**Contexto:** {context if context else "Sin contexto"}

Responde claro, como la gente de barrio, natural y chevere. Máximo 2-3 párrafos."""
            
            try:
                response = self.model.generate_content([prompt, video_file])
            except ResourceExhausted:
                logger.warning("Gemini: cuota excedida en process_video")
                return MSG_CUOTA_EXCEDIDA
            
            if response.text:
                logger.info("Video procesado exitosamente con Gemini")
                return response.text.strip()
            return "No pude procesar el video en este momento."
        
        except Exception as e:
            logger.error(f"Error procesando video: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error al analizar el video. Verifica que sea formato MP4 o similar."
    
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
            try:
                response = self.model.generate_content([prompt, audio_file])
            except ResourceExhausted:
                logger.warning("Gemini: cuota excedida en transcribe_audio")
                return None
            
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
            
            try:
                response = self.model.generate_content(prompt)
            except ResourceExhausted:
                return {'sentiment': 'neutral', 'score': 0.5}
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
