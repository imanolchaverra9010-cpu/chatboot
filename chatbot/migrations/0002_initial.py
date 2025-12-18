# Generated migration file for business models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0001_initial'),  # Ajusta según tu migración anterior
    ]

    operations = [
        # Categorías de Negocio
        migrations.CreateModel(
            name='CategoriaNegocio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('descripcion', models.TextField(blank=True)),
                ('icono', models.CharField(blank=True, help_text='Emoji o nombre de icono', max_length=50)),
                ('orden', models.IntegerField(default=0)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Categoría de Negocio',
                'verbose_name_plural': 'Categorías de Negocio',
                'db_table': 'categorias_negocio',
                'ordering': ['orden', 'nombre'],
            },
        ),
        
        # Negocios
        migrations.CreateModel(
            name='Negocio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('descripcion', models.TextField(blank=True)),
                ('categoria', models.CharField(blank=True, max_length=100)),
                ('direccion', models.TextField()),
                ('ciudad', models.CharField(default='Quibdó', max_length=100)),
                ('barrio', models.CharField(blank=True, max_length=100)),
                ('latitud', models.DecimalField(blank=True, decimal_places=8, max_digits=10, null=True)),
                ('longitud', models.DecimalField(blank=True, decimal_places=8, max_digits=11, null=True)),
                ('referencia_ubicacion', models.TextField(blank=True, help_text='Ej: Frente al parque principal')),
                ('telefono', models.CharField(blank=True, max_length=20)),
                ('whatsapp', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('facebook', models.URLField(blank=True)),
                ('instagram', models.CharField(blank=True, max_length=100)),
                ('sitio_web', models.URLField(blank=True)),
                ('logo', models.URLField(blank=True, help_text='URL del logo')),
                ('imagen_portada', models.URLField(blank=True)),
                ('activo', models.BooleanField(default=True)),
                ('verificado', models.BooleanField(default=False)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Negocio',
                'verbose_name_plural': 'Negocios',
                'db_table': 'negocios',
                'ordering': ['nombre'],
            },
        ),
        
        # Horarios de Atención
        migrations.CreateModel(
            name='HorarioAtencion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dia_semana', models.CharField(choices=[('lunes', 'Lunes'), ('martes', 'Martes'), ('miercoles', 'Miércoles'), ('jueves', 'Jueves'), ('viernes', 'Viernes'), ('sabado', 'Sábado'), ('domingo', 'Domingo')], max_length=10)),
                ('hora_apertura', models.TimeField()),
                ('hora_cierre', models.TimeField()),
                ('cerrado', models.BooleanField(default=False, help_text='Marcar si el negocio está cerrado este día')),
                ('notas', models.CharField(blank=True, help_text='Ej: Cerrado por almuerzo de 12-2pm', max_length=255)),
                ('negocio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='horarios', to='chatbot.negocio')),
            ],
            options={
                'verbose_name': 'Horario de Atención',
                'verbose_name_plural': 'Horarios de Atención',
                'db_table': 'horarios_atencion',
                'ordering': ['negocio', 'dia_semana'],
                'unique_together': {('negocio', 'dia_semana')},
            },
        ),
        
        # Productos de Negocio
        migrations.CreateModel(
            name='ProductoNegocio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('descripcion', models.TextField(blank=True)),
                ('precio', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('precio_desde', models.DecimalField(blank=True, decimal_places=2, help_text='Para rangos de precios', max_digits=10, null=True)),
                ('precio_hasta', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('categoria', models.CharField(blank=True, max_length=100)),
                ('disponible', models.BooleanField(default=True)),
                ('stock', models.IntegerField(blank=True, help_text='Dejar en blanco si no aplica', null=True)),
                ('imagen', models.URLField(blank=True)),
                ('destacado', models.BooleanField(default=False)),
                ('orden', models.IntegerField(default=0, help_text='Para ordenar productos')),
                ('activo', models.BooleanField(default=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('negocio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productos', to='chatbot.negocio')),
            ],
            options={
                'verbose_name': 'Producto/Servicio',
                'verbose_name_plural': 'Productos/Servicios',
                'db_table': 'productos_negocio',
                'ordering': ['negocio', '-destacado', 'orden', 'nombre'],
            },
        ),
        
        # Reseñas de Negocio
        migrations.CreateModel(
            name='ResenaNegocio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telefono_cliente', models.CharField(max_length=20)),
                ('nombre_cliente', models.CharField(blank=True, max_length=100)),
                ('calificacion', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], help_text='1-5 estrellas')),
                ('comentario', models.TextField(blank=True)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('aprobado', models.BooleanField(default=False)),
                ('negocio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resenas', to='chatbot.negocio')),
            ],
            options={
                'verbose_name': 'Reseña',
                'verbose_name_plural': 'Reseñas',
                'db_table': 'resenas_negocio',
                'ordering': ['-fecha'],
            },
        ),
    ]
