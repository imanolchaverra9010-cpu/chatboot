"""
Modelos para almacenar conversaciones, mensajes y datos de negocios
"""
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    """Conversación con un usuario de WhatsApp"""
    phone_number = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Conversación'
        verbose_name_plural = 'Conversaciones'
    
    def __str__(self):
        return f"{self.name or self.phone_number}"
    
    def get_recent_messages(self, limit=10):
        """Obtener mensajes recientes para contexto"""
        return self.messages.order_by('-created_at')[:limit]


class Message(models.Model):
    """Mensaje individual en una conversación"""
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('image', 'Imagen'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Documento'),
        ('location', 'Ubicación'),
        ('sticker', 'Sticker'),
        ('unknown', 'Desconocido'),
    ]
    
    DIRECTION_CHOICES = [
        ('incoming', 'Entrante'),
        ('outgoing', 'Saliente'),
    ]
    
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    message_id = models.CharField(max_length=100, unique=True, db_index=True)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField()
    media_url = models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Metadata adicional
    status = models.CharField(max_length=20, blank=True, default='sent')
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
    
    def __str__(self):
        return f"{self.conversation.phone_number} - {self.message_type} - {self.direction}"


class BotContext(models.Model):
    """Contexto persistente para cada conversación"""
    conversation = models.OneToOneField(
        Conversation,
        on_delete=models.CASCADE,
        related_name='context'
    )
    context_data = models.JSONField(default=dict)
    last_intent = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Contexto de Bot'
        verbose_name_plural = 'Contextos de Bot'
    
    def __str__(self):
        return f"Context for {self.conversation.phone_number}"


# --- MODELOS DE NEGOCIOS ---

class Negocio(models.Model):
    """Negocio o establecimiento comercial"""
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=100, blank=True, help_text="Ej: Restaurante, Tienda, Farmacia")
    
    # Ubicación
    direccion = models.TextField()
    ciudad = models.CharField(max_length=100, default='Quibdó')
    barrio = models.CharField(max_length=100, blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitud = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    referencia_ubicacion = models.TextField(blank=True, help_text="Ej: Frente al parque principal")
    
    # Contacto
    telefono = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    sitio_web = models.URLField(blank=True)
    
    # Información adicional
    logo = models.URLField(blank=True, help_text="URL del logo")
    imagen_portada = models.URLField(blank=True)
    activo = models.BooleanField(default=True)
    verificado = models.BooleanField(default=False)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'negocios'
        verbose_name = 'Negocio'
        verbose_name_plural = 'Negocios'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class HorarioAtencion(models.Model):
    """Horarios de atención de un negocio"""
    DIAS_SEMANA = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
    ]
    
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.CharField(max_length=10, choices=DIAS_SEMANA)
    hora_apertura = models.TimeField()
    hora_cierre = models.TimeField()
    cerrado = models.BooleanField(default=False, help_text="Marcar si el negocio está cerrado este día")
    notas = models.CharField(max_length=255, blank=True, help_text="Ej: Cerrado por almuerzo de 12-2pm")
    
    class Meta:
        db_table = 'horarios_atencion'
        verbose_name = 'Horario de Atención'
        verbose_name_plural = 'Horarios de Atención'
        ordering = ['negocio', 'dia_semana']
        unique_together = ['negocio', 'dia_semana']
    
    def __str__(self):
        if self.cerrado:
            return f"{self.negocio.nombre} - {self.dia_semana}: Cerrado"
        return f"{self.negocio.nombre} - {self.dia_semana}: {self.hora_apertura} - {self.hora_cierre}"


class ProductoNegocio(models.Model):
    """Producto o servicio ofrecido por un negocio"""
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='productos')
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_desde = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                       help_text="Para rangos de precios")
    precio_hasta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    categoria = models.CharField(max_length=100, blank=True)
    
    # Disponibilidad
    disponible = models.BooleanField(default=True)
    stock = models.IntegerField(null=True, blank=True, help_text="Dejar en blanco si no aplica")
    
    # Multimedia
    imagen = models.URLField(blank=True)
    
    # Metadata
    destacado = models.BooleanField(default=False)
    orden = models.IntegerField(default=0, help_text="Para ordenar productos")
    activo = models.BooleanField(default=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'productos_negocio'
        verbose_name = 'Producto/Servicio'
        verbose_name_plural = 'Productos/Servicios'
        ordering = ['negocio', '-destacado', 'orden', 'nombre']
    
    def __str__(self):
        return f"{self.negocio.nombre} - {self.nombre}"
    
    def get_precio_display(self):
        """Retorna el precio formateado"""
        if self.precio:
            return f"${self.precio:,.0f}"
        elif self.precio_desde and self.precio_hasta:
            return f"${self.precio_desde:,.0f} - ${self.precio_hasta:,.0f}"
        elif self.precio_desde:
            return f"Desde ${self.precio_desde:,.0f}"
        return "Consultar precio"


class CategoriaNegocio(models.Model):
    """Categorías para clasificar negocios"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    icono = models.CharField(max_length=50, blank=True, help_text="Emoji o nombre de icono")
    orden = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'categorias_negocio'
        verbose_name = 'Categoría de Negocio'
        verbose_name_plural = 'Categorías de Negocio'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre


class ResenaNegocio(models.Model):
    """Reseñas y calificaciones de negocios"""
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='resenas')
    telefono_cliente = models.CharField(max_length=20)
    nombre_cliente = models.CharField(max_length=100, blank=True)
    calificacion = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text="1-5 estrellas")
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    aprobado = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'resenas_negocio'
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.negocio.nombre} - {self.calificacion}⭐ por {self.nombre_cliente or self.telefono_cliente}"


# --- MODELOS ORIGINALES DE ÉBANO COMPANY (COMPATIBILIDAD) ---

class Cliente(models.Model):
    """Cliente de Ébano Company"""
    nombre = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'clientes'
        managed = False
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Producto disponible en el catálogo"""
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    categoria = models.CharField(max_length=100, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'productos'
        managed = False
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
    
    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    """Pedido realizado por un cliente"""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=50)
    direccion_envio = models.TextField(blank=True)
    notas = models.TextField(blank=True)
    
    class Meta:
        db_table = 'pedidos'
        managed = False
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente.nombre}"


class DetallePedido(models.Model):
    """Detalle de productos en un pedido"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'detalle_pedidos'
        managed = False
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedidos'
    
    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"