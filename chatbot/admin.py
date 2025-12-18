"""
Configuración del panel de administración de Django
"""
from django.contrib import admin
from .models import (
    Conversation, Message, BotContext,
    Negocio, HorarioAtencion, ProductoNegocio, 
    CategoriaNegocio, ResenaNegocio
)


# ==================== CHATBOT ====================

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'name', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['phone_number', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('messages')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'direction', 'message_type', 'content_preview', 'timestamp']
    list_filter = ['direction', 'message_type', 'status', 'timestamp']
    search_fields = ['conversation__phone_number', 'content']
    readonly_fields = ['message_id', 'timestamp', 'created_at']
    date_hierarchy = 'timestamp'
    
    def content_preview(self, obj):
        """Mostrar vista previa del contenido"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenido'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('conversation')


@admin.register(BotContext)
class BotContextAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'last_intent', 'updated_at']
    search_fields = ['conversation__phone_number', 'last_intent']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('conversation')


# ==================== NEGOCIOS ====================

class HorarioAtencionInline(admin.TabularInline):
    model = HorarioAtencion
    extra = 7
    max_num = 7
    fields = ['dia_semana', 'hora_apertura', 'hora_cierre', 'cerrado', 'notas']


class ProductoNegocioInline(admin.TabularInline):
    model = ProductoNegocio
    extra = 1
    fields = ['nombre', 'precio', 'disponible', 'destacado', 'orden']
    show_change_link = True


@admin.register(Negocio)
class NegocioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'ciudad', 'barrio', 'telefono', 'activo', 'verificado']
    list_filter = ['activo', 'verificado', 'categoria', 'ciudad']
    search_fields = ['nombre', 'descripcion', 'categoria', 'direccion', 'barrio']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'categoria', 'activo', 'verificado')
        }),
        ('Ubicación', {
            'fields': ('direccion', 'ciudad', 'barrio', 'referencia_ubicacion', 'latitud', 'longitud')
        }),
        ('Contacto', {
            'fields': ('telefono', 'whatsapp', 'email', 'facebook', 'instagram', 'sitio_web')
        }),
        ('Multimedia', {
            'fields': ('logo', 'imagen_portada'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [HorarioAtencionInline, ProductoNegocioInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('horarios', 'productos')


@admin.register(HorarioAtencion)
class HorarioAtencionAdmin(admin.ModelAdmin):
    list_display = ['negocio', 'dia_semana', 'hora_apertura', 'hora_cierre', 'cerrado']
    list_filter = ['dia_semana', 'cerrado']
    search_fields = ['negocio__nombre']
    list_select_related = ['negocio']


@admin.register(ProductoNegocio)
class ProductoNegocioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'negocio', 'precio_display', 'categoria', 'disponible', 'destacado', 'activo']
    list_filter = ['disponible', 'destacado', 'activo', 'categoria', 'negocio']
    search_fields = ['nombre', 'descripcion', 'negocio__nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    list_select_related = ['negocio']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('negocio', 'nombre', 'descripcion', 'categoria')
        }),
        ('Precio', {
            'fields': ('precio', 'precio_desde', 'precio_hasta')
        }),
        ('Disponibilidad', {
            'fields': ('disponible', 'stock', 'activo')
        }),
        ('Destacado y Orden', {
            'fields': ('destacado', 'orden')
        }),
        ('Multimedia', {
            'fields': ('imagen',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def precio_display(self, obj):
        """Mostrar precio formateado"""
        return obj.get_precio_display()
    precio_display.short_description = 'Precio'


@admin.register(CategoriaNegocio)
class CategoriaNegocioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'icono', 'orden', 'activo']
    list_filter = ['activo']
    search_fields = ['nombre', 'descripcion']
    ordering = ['orden', 'nombre']


@admin.register(ResenaNegocio)
class ResenaNegocioAdmin(admin.ModelAdmin):
    list_display = ['negocio', 'nombre_cliente', 'calificacion', 'fecha', 'aprobado']
    list_filter = ['calificacion', 'aprobado', 'fecha']
    search_fields = ['negocio__nombre', 'nombre_cliente', 'telefono_cliente', 'comentario']
    readonly_fields = ['fecha']
    list_select_related = ['negocio']
    date_hierarchy = 'fecha'
    
    actions = ['aprobar_resenas', 'rechazar_resenas']
    
    def aprobar_resenas(self, request, queryset):
        """Aprobar reseñas seleccionadas"""
        count = queryset.update(aprobado=True)
        self.message_user(request, f'{count} reseña(s) aprobada(s).')
    aprobar_resenas.short_description = "Aprobar reseñas seleccionadas"
    
    def rechazar_resenas(self, request, queryset):
        """Rechazar reseñas seleccionadas"""
        count = queryset.update(aprobado=False)
        self.message_user(request, f'{count} reseña(s) rechazada(s).')
    rechazar_resenas.short_description = "Rechazar reseñas seleccionadas"