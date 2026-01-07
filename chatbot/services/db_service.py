"""
Servicio MEJORADO para consultar la base de datos de Negocios
"""
import logging
from django.db import connection
from django.db.models import Q, Count, Sum, Avg
from datetime import datetime, time
from ..models import (
    Negocio, HorarioAtencion, ProductoNegocio, CategoriaNegocio, ResenaNegocio,
    EventoDeportivo,
    Cliente, Producto, Pedido, DetallePedido
)

logger = logging.getLogger('chatbot')


class DatabaseService:
    """Servicio para operaciones de base de datos - VERSIÓN MEJORADA"""
    
    # ==================== MÉTODOS PARA NEGOCIOS ====================
    
    @staticmethod
    def buscar_negocios(query=None, categoria=None, ciudad='Quibdó', activos=True, limit=1000):
        """
        Buscar negocios por nombre, categoría o ciudad
        """
        try:
            negocios = Negocio.objects.all()
            
            if activos:
                negocios = negocios.filter(activo=True)
            
            if ciudad:
                negocios = negocios.filter(ciudad__icontains=ciudad)
            
            if categoria:
                negocios = negocios.filter(categoria__icontains=categoria)
            
            if query:
                negocios = negocios.filter(
                    Q(nombre__icontains=query) | 
                    Q(descripcion__icontains=query) |
                    Q(categoria__icontains=query) |
                    Q(barrio__icontains=query)
                )
            
            return negocios.order_by('-verificado', 'nombre')[:limit]
        except Exception as e:
            logger.error(f"Error buscando negocios: {e}")
            return []
    
    @staticmethod
    def obtener_negocio_por_id(negocio_id):
        """Obtener negocio específico por ID"""
        try:
            return Negocio.objects.get(id=negocio_id, activo=True)
        except Negocio.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo negocio: {e}")
            return None
    
    @staticmethod
    def obtener_negocio_por_nombre(nombre):
        """Buscar negocio por nombre exacto o similar"""
        try:
            # Primero intenta nombre exacto
            negocio = Negocio.objects.filter(
                nombre__iexact=nombre,
                activo=True
            ).first()
            
            if negocio:
                return negocio
            
            # Si no, busca similar
            negocio = Negocio.objects.filter(
                nombre__icontains=nombre,
                activo=True
            ).first()
            
            return negocio
        except Exception as e:
            logger.error(f"Error obteniendo negocio por nombre: {e}")
            return None
    
    @staticmethod
    def obtener_horarios_negocio(negocio_id):
        """Obtener horarios de atención de un negocio"""
        try:
            return HorarioAtencion.objects.filter(negocio_id=negocio_id).order_by('dia_semana')
        except Exception as e:
            logger.error(f"Error obteniendo horarios: {e}")
            return []
    
    @staticmethod
    def verificar_negocio_abierto(negocio_id):
        """Verificar si un negocio está abierto en el momento actual"""
        try:
            dias_map = {
                0: 'lunes', 1: 'martes', 2: 'miercoles', 3: 'jueves',
                4: 'viernes', 5: 'sabado', 6: 'domingo'
            }
            
            ahora = datetime.now()
            dia_actual = dias_map[ahora.weekday()]
            hora_actual = ahora.time()
            
            horario = HorarioAtencion.objects.filter(
                negocio_id=negocio_id,
                dia_semana=dia_actual
            ).first()
            
            if not horario:
                return {'abierto': None, 'mensaje': 'No hay información de horario para hoy'}
            
            if horario.cerrado:
                return {'abierto': False, 'mensaje': f'Cerrado los {dia_actual}s'}
            
            abierto = horario.hora_apertura <= hora_actual <= horario.hora_cierre
            
            if abierto:
                return {
                    'abierto': True,
                    'mensaje': f'Abierto hasta las {horario.hora_cierre.strftime("%I:%M %p")}',
                    'horario': horario
                }
            else:
                return {
                    'abierto': False,
                    'mensaje': f'Abre a las {horario.hora_apertura.strftime("%I:%M %p")}',
                    'horario': horario
                }
        except Exception as e:
            logger.error(f"Error verificando apertura: {e}")
            return {'abierto': None, 'mensaje': 'Error al verificar horario'}
    
    @staticmethod
    def obtener_productos_negocio(negocio_id, disponibles=True, limit=1000):
        """Obtener productos/servicios de un negocio"""
        try:
            productos = ProductoNegocio.objects.filter(
                negocio_id=negocio_id,
                activo=True
            )
            
            if disponibles:
                productos = productos.filter(disponible=True)
            
            return productos.order_by('-destacado', 'orden', 'nombre')[:limit]
        except Exception as e:
            logger.error(f"Error obteniendo productos: {e}")
            return []
    
    @staticmethod
    def buscar_productos_negocio(negocio_id, query):
        """Buscar productos específicos en un negocio"""
        try:
            return ProductoNegocio.objects.filter(
                negocio_id=negocio_id,
                activo=True,
                disponible=True
            ).filter(
                Q(nombre__icontains=query) | 
                Q(descripcion__icontains=query) |
                Q(categoria__icontains=query)
            )
        except Exception as e:
            logger.error(f"Error buscando productos: {e}")
            return []
    
    @staticmethod
    def buscar_productos_globalmente(query, limit=20):
        """Buscar productos en todos los negocios"""
        try:
            return ProductoNegocio.objects.filter(
                Q(nombre__icontains=query) | 
                Q(descripcion__icontains=query) |
                Q(categoria__icontains=query),
                activo=True,
                disponible=True
            ).select_related('negocio').order_by('-destacado', 'nombre')[:limit]
        except Exception as e:
            logger.error(f"Error buscando productos globalmente: {e}")
            return []
    
    @staticmethod
    def obtener_categorias_negocios():
        """Obtener lista de categorías de negocios"""
        try:
            # Primero intentar con tabla de categorías
            categorias_tabla = CategoriaNegocio.objects.filter(activo=True).order_by('orden', 'nombre')
            if categorias_tabla.exists():
                return list(categorias_tabla)
            
            # Si no hay, extraer de los negocios existentes
            categorias = Negocio.objects.filter(
                activo=True,
                categoria__isnull=False
            ).values_list('categoria', flat=True).distinct()
            
            return [c for c in categorias if c]
        except Exception as e:
            logger.error(f"Error obteniendo categorías: {e}")
            return []
    
    @staticmethod
    def obtener_resenas_negocio(negocio_id, aprobadas=True, limit=1000):
        """Obtener reseñas de un negocio"""
        try:
            resenas = ResenaNegocio.objects.filter(negocio_id=negocio_id)
            
            if aprobadas:
                resenas = resenas.filter(aprobado=True)
            
            return resenas.order_by('-fecha')[:limit]
        except Exception as e:
            logger.error(f"Error obteniendo reseñas: {e}")
            return []
    
    @staticmethod
    def obtener_calificacion_promedio(negocio_id):
        """Obtener calificación promedio de un negocio"""
        try:
            resultado = ResenaNegocio.objects.filter(
                negocio_id=negocio_id,
                aprobado=True
            ).aggregate(Avg('calificacion'))
            
            return resultado['calificacion__avg']
        except Exception as e:
            logger.error(f"Error calculando calificación: {e}")
            return None
    
    @staticmethod
    def crear_resena(negocio_id, telefono_cliente, calificacion, comentario='', nombre_cliente=''):
        """Crear una nueva reseña"""
        try:
            resena = ResenaNegocio.objects.create(
                negocio_id=negocio_id,
                telefono_cliente=telefono_cliente,
                nombre_cliente=nombre_cliente,
                calificacion=calificacion,
                comentario=comentario,
                aprobado=False  # Requiere aprobación
            )
            logger.info(f"Reseña creada: {resena.id} para negocio {negocio_id}")
            return resena
        except Exception as e:
            logger.error(f"Error creando reseña: {e}")
            return None
    
    @staticmethod
    def obtener_estadisticas_negocio(negocio_id):
        """Obtener estadísticas completas de un negocio"""
        try:
            negocio = Negocio.objects.get(id=negocio_id)
            
            # Cantidad de productos
            total_productos = ProductoNegocio.objects.filter(
                negocio_id=negocio_id,
                activo=True
            ).count()
            
            # Cantidad de reseñas
            total_resenas = ResenaNegocio.objects.filter(
                negocio_id=negocio_id,
                aprobado=True
            ).count()
            
            # Calificación promedio
            calificacion_promedio = DatabaseService.obtener_calificacion_promedio(negocio_id)
            
            # Distribución de calificaciones
            distribucion = ResenaNegocio.objects.filter(
                negocio_id=negocio_id,
                aprobado=True
            ).values('calificacion').annotate(
                cantidad=Count('id')
            ).order_by('-calificacion')
            
            return {
                'negocio': negocio,
                'total_productos': total_productos,
                'total_resenas': total_resenas,
                'calificacion_promedio': calificacion_promedio,
                'distribucion_calificaciones': list(distribucion)
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return None
    
    @staticmethod
    def buscar_negocios_cercanos(barrio=None, referencia=None, limit=1000):
        """Buscar negocios por ubicación aproximada"""
        try:
            negocios = Negocio.objects.filter(activo=True)
            
            if barrio:
                negocios = negocios.filter(barrio__icontains=barrio)
            
            if referencia:
                negocios = negocios.filter(
                    Q(referencia_ubicacion__icontains=referencia) |
                    Q(direccion__icontains=referencia)
                )
            
            return negocios.order_by('-verificado', 'nombre')[:limit]
        except Exception as e:
            logger.error(f"Error buscando negocios cercanos: {e}")
            return []
    
    @staticmethod
    def obtener_info_completa_negocio(negocio_id):
        """Obtener información completa de un negocio"""
        try:
            negocio = Negocio.objects.get(id=negocio_id, activo=True)
            horarios = list(HorarioAtencion.objects.filter(negocio=negocio))
            productos = list(ProductoNegocio.objects.filter(
                negocio=negocio, 
                activo=True
            ).order_by('-destacado', 'orden')[:10])
            
            calificacion = DatabaseService.obtener_calificacion_promedio(negocio_id)
            estado_apertura = DatabaseService.verificar_negocio_abierto(negocio_id)
            resenas = list(DatabaseService.obtener_resenas_negocio(negocio_id, limit=5))
            
            return {
                'negocio': negocio,
                'horarios': horarios,
                'productos': productos,
                'calificacion_promedio': calificacion,
                'estado_apertura': estado_apertura,
                'resenas_recientes': resenas
            }
        except Negocio.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo info completa: {e}")
            return None
    
    @staticmethod
    def obtener_negocios_abiertos_ahora(categoria=None):
        """Obtener lista de negocios que están abiertos en este momento"""
        try:
            dias_map = {
                0: 'lunes', 1: 'martes', 2: 'miercoles', 3: 'jueves',
                4: 'viernes', 5: 'sabado', 6: 'domingo'
            }
            
            ahora = datetime.now()
            dia_actual = dias_map[ahora.weekday()]
            hora_actual = ahora.time()
            
            # Obtener horarios de hoy
            horarios_hoy = HorarioAtencion.objects.filter(
                dia_semana=dia_actual,
                cerrado=False,
                hora_apertura__lte=hora_actual,
                hora_cierre__gte=hora_actual
            ).select_related('negocio')
            
            # Filtrar por categoría si se especifica
            if categoria:
                horarios_hoy = horarios_hoy.filter(
                    negocio__categoria__icontains=categoria
                )
            
            # Extraer negocios únicos
            negocios_abiertos = []
            negocios_ids = set()
            
            for horario in horarios_hoy:
                if horario.negocio.activo and horario.negocio.id not in negocios_ids:
                    negocios_abiertos.append(horario.negocio)
                    negocios_ids.add(horario.negocio.id)
            
            return negocios_abiertos
        except Exception as e:
            logger.error(f"Error obteniendo negocios abiertos: {e}")
            return []
    
    # ==================== MÉTODOS PARA EVENTOS DEPORTIVOS ====================
    
    @staticmethod
    def obtener_eventos_proximos(dias=7, tipo_evento=None, limit=10):
        """Obtener eventos deportivos próximos"""
        try:
            from datetime import datetime, timedelta
            
            ahora = datetime.now()
            fecha_limite = ahora + timedelta(days=dias)
            
            eventos = EventoDeportivo.objects.filter(
                activo=True,
                fecha_evento__gte=ahora,
                fecha_evento__lte=fecha_limite
            )
            
            if tipo_evento:
                eventos = eventos.filter(tipo_evento__icontains=tipo_evento)
            
            return eventos.order_by('fecha_evento')[:limit]
        except Exception as e:
            logger.error(f"Error obteniendo eventos próximos: {e}")
            return []
    
    @staticmethod
    def buscar_eventos(query=None, tipo_evento=None, limit=10):
        """Buscar eventos deportivos"""
        try:
            from datetime import datetime
            
            eventos = EventoDeportivo.objects.filter(
                activo=True,
                fecha_evento__gte=datetime.now()
            )
            
            if tipo_evento:
                eventos = eventos.filter(tipo_evento__icontains=tipo_evento)
            
            if query:
                eventos = eventos.filter(
                    Q(nombre__icontains=query) |
                    Q(descripcion__icontains=query) |
                    Q(equipo_local__icontains=query) |
                    Q(equipo_visitante__icontains=query) |
                    Q(lugar__icontains=query)
                )
            
            return eventos.order_by('fecha_evento')[:limit]
        except Exception as e:
            logger.error(f"Error buscando eventos: {e}")
            return []
    
    @staticmethod
    def obtener_evento_por_id(evento_id):
        """Obtener evento específico por ID"""
        try:
            return EventoDeportivo.objects.get(id=evento_id, activo=True)
        except EventoDeportivo.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo evento: {e}")
            return None
    
    # ==================== MÉTODOS ORIGINALES (COMPATIBILIDAD) ====================
    
    @staticmethod
    def buscar_cliente(telefono=None, email=None, nombre=None):
        """Buscar cliente por teléfono, email o nombre"""
        try:
            if telefono:
                return Cliente.objects.filter(telefono__icontains=telefono).first()
            if email:
                return Cliente.objects.filter(email__iexact=email).first()
            if nombre:
                return Cliente.objects.filter(nombre__icontains=nombre).first()
        except Exception as e:
            logger.error(f"Error buscando cliente: {e}")
        return None
    
    @staticmethod
    def listar_productos(categoria=None, disponibles=True, limit=1000):
        """Listar productos con filtros opcionales"""
        try:
            query = Producto.objects.filter(activo=True)
            
            if categoria:
                query = query.filter(categoria__icontains=categoria)
            
            if disponibles:
                query = query.filter(stock__gt=0)
            
            return query.order_by('-fecha_creacion')[:limit]
        except Exception as e:
            logger.error(f"Error listando productos: {e}")
            return []
    
    @staticmethod
    def buscar_producto(nombre):
        """Buscar productos por nombre"""
        try:
            return Producto.objects.filter(
                Q(nombre__icontains=nombre) | Q(descripcion__icontains=nombre),
                activo=True
            )
        except Exception as e:
            logger.error(f"Error buscando producto: {e}")
            return []
    
    @staticmethod
    def obtener_producto_por_id(producto_id):
        """Obtener producto específico por ID"""
        try:
            return Producto.objects.get(id=producto_id, activo=True)
        except Producto.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo producto: {e}")
            return None
    
    @staticmethod
    def verificar_stock(producto_id, cantidad=1):
        """Verificar si hay stock suficiente"""
        try:
            producto = Producto.objects.get(id=producto_id)
            return producto.stock >= cantidad
        except Exception as e:
            logger.error(f"Error verificando stock: {e}")
            return False
    
    @staticmethod
    def obtener_pedidos_cliente(cliente_id, limit=1000):
        """Obtener pedidos de un cliente"""
        try:
            return Pedido.objects.filter(
                cliente_id=cliente_id
            ).order_by('-fecha_pedido')[:limit]
        except Exception as e:
            logger.error(f"Error obteniendo pedidos: {e}")
            return []
    
    @staticmethod
    def obtener_detalle_pedido(pedido_id):
        """Obtener detalles completos de un pedido"""
        try:
            pedido = Pedido.objects.select_related('cliente').get(id=pedido_id)
            detalles = DetallePedido.objects.filter(pedido=pedido).select_related('producto')
            
            return {
                'pedido': pedido,
                'detalles': detalles,
                'total_items': detalles.count()
            }
        except Pedido.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error obteniendo detalle pedido: {e}")
            return None
