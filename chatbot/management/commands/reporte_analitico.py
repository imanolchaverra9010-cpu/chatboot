"""
Comando para generar reporte analítico (Power in Data)
Caracterización de usuarios, tendencias, mapa de calor, segmentación
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from chatbot.models import ConsultaAnalitica, Message, Conversation
from chatbot.services.db_service import DatabaseService


class Command(BaseCommand):
    help = 'Genera reporte analítico: tendencias, segmentación por barrio, motivos de consulta'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=7,
            help='Días hacia atrás para el reporte (default: 7)'
        )

    def handle(self, *args, **options):
        dias = options['dias']
        desde = timezone.now() - timezone.timedelta(days=dias)

        self.stdout.write(self.style.SUCCESS(f'\n=== REPORTE ANALÍTICO (últimos {dias} días) ===\n'))

        # 1. Tendencias de consultas
        self.stdout.write('📊 TENDENCIAS DE CONSULTAS (por motivo):')
        tendencias = ConsultaAnalitica.objects.filter(
            fecha_consulta__gte=desde
        ).values('motivo_consulta').annotate(
            total=Count('id')
        ).order_by('-total')[:15]

        for t in tendencias:
            motivo = t['motivo_consulta'] or '(sin clasificar)'
            self.stdout.write(f"  • {motivo[:50]}: {t['total']} consultas")

        # 2. Segmentación por barrio
        self.stdout.write('\n🗺️ SEGMENTACIÓN POR BARRIO:')
        segmentacion = ConsultaAnalitica.objects.filter(
            fecha_consulta__gte=desde
        ).exclude(barrio='').exclude(barrio__isnull=True).values(
            'barrio'
        ).annotate(total=Count('id')).order_by('-total')[:10]

        if segmentacion:
            for s in segmentacion:
                self.stdout.write(f"  • {s['barrio']}: {s['total']} consultas")
        else:
            self.stdout.write('  (Sin datos de barrio)')

        # 3. Mapa de calor: intents más consultados
        self.stdout.write('\n🔥 MAPA DE CALOR (intents más consultados):')
        intents = ConsultaAnalitica.objects.filter(
            fecha_consulta__gte=desde
        ).exclude(intent_detectado='').values(
            'intent_detectado'
        ).annotate(total=Count('id')).order_by('-total')[:10]

        for i in intents:
            self.stdout.write(f"  • {i['intent_detectado'] or 'general'}: {i['total']}")

        # 4. Casos escalados
        escalados = ConsultaAnalitica.objects.filter(
            fecha_consulta__gte=desde,
            escalado_humano=True
        ).count()
        self.stdout.write(f'\n📤 CASOS ESCALADOS A HUMANO: {escalados}')

        # 5. Tasa de resolución
        total = ConsultaAnalitica.objects.filter(fecha_consulta__gte=desde).count()
        resueltos = ConsultaAnalitica.objects.filter(
            fecha_consulta__gte=desde,
            resuelto=True
        ).count()
        tasa = (resueltos / total * 100) if total > 0 else 0
        self.stdout.write(f'✅ TASA DE RESOLUCIÓN: {tasa:.1f}% ({resueltos}/{total})')

        self.stdout.write(self.style.SUCCESS('\n=== Fin del reporte ===\n'))
