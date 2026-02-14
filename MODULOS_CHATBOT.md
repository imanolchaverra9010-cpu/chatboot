# Módulos del Chatbot - Implementación Completa

El chatbot ahora soporta todos los módulos solicitados para ciudadanía, logística, analítica y escalamiento.

---

## 📋 Módulo Informativo (Ciudadanía)

| Funcionalidad | Implementación | Cómo usarlo |
|---------------|----------------|-------------|
| **1. Ubicación de locales/escenarios** | `Negocio`, `EventoDeportivo` en BD. Búsqueda por nombre, barrio, categoría. | Preguntar: "¿Dónde queda [nombre]?", "Negocios en [barrio]" |
| **2. Horarios de atención** | `HorarioAtencion` por negocio. Estado abierto/cerrado en tiempo real. | "¿Horario de [negocio]?", "¿Está abierto?" |
| **3. Agenda de eventos** | `EventoDeportivo`. Eventos próximos por tipo (fútbol, baloncesto, etc.) | "¿Qué eventos hay?", "Partidos de fútbol" |
| **4. Boletería** | Modelo `Boleteria` con precios, puntos de venta, links de compra | "¿Cuánto cuesta la entrada?", "Link para comprar boletos" |
| **5. Requisitos de trámites** | Modelo `TramiteRequisitos` con requisitos, documentos, links de turnos | "¿Qué necesito para [trámite]?", "Requisitos para [certificado]" |

---

## 🚚 Módulo Logístico

| Funcionalidad | Implementación | Cómo usarlo |
|---------------|----------------|-------------|
| **1. Turnos** | Modelo `Turno`. Reservar y cancelar por comando. | "turnos" → ver disponibles. "reservar turno 5" / "cancelar turno 5" |
| **2. Cómo llegar** | Links de Google Maps generados desde dirección o coordenadas | "¿Cómo llego a [lugar]?", "Ruta a [negocio/evento]" |
| **3. Alertas de última hora** | Modelo `Alerta`. Se incluyen siempre en el contexto del bot | Se muestran automáticamente si hay alertas activas |

---

## 📊 Módulo Analítico (Power in Data)

| Funcionalidad | Implementación | Cómo acceder |
|---------------|----------------|--------------|
| **1. Caracterización de usuarios** | `ConsultaAnalitica` con phone, motivo, intent, barrio, edad | Django Admin + reporte |
| **2. Tendencias de consultas** | Registro por consulta. Agregación por motivo e intent | `python manage.py reporte_analitico` |
| **3. Mapa de calor de intereses** | Intents más consultados en el reporte | `python manage.py reporte_analitico --dias 30` |
| **4. Segmentación** | Por barrio, edad, motivo de consulta | Django Admin → ConsultaAnalitica |

**Comando de reporte:**
```bash
python manage.py reporte_analitico --dias 7
```

---

## 🔄 Módulo de Escalamiento

| Funcionalidad | Implementación | Cómo usarlo |
|---------------|----------------|-------------|
| **1. Envío a humano** | Usuario escribe `HUMANO` o "hablar con humano" | El bot registra el escalamiento y da número de asesor (si está configurado) |
| **2. Casos no resueltos → feedback** | Modelo `Escalamiento` con feedback_sistema y resuelto_por_bot | El bot sugiere "Escribe *HUMANO* para hablar con un asesor" cuando no puede resolver |

**Configuración:**
- Variable de entorno: `ESCALAMIENTO_WHATSAPP` = número de WhatsApp del asesor
- El bot indica ese número al usuario cuando escala

---

## 🗄️ Nuevos Modelos (Django Admin)

- **Boleteria**: Precios, puntos de venta, links de compra para eventos
- **TramiteRequisitos**: Requisitos de trámites, documentos, links
- **Turno**: Turnos disponibles para reservar/cancelar
- **Alerta**: Alertas y cambios de última hora
- **ConsultaAnalitica**: Registro de cada consulta para analytics
- **Escalamiento**: Casos escalados a humano

---

## ⚙️ Pasos para activar

1. **Migraciones:**
   ```bash
   python manage.py makemigrations chatbot
   python manage.py migrate
   ```

2. **Datos iniciales:** Crear registros en Django Admin para:
   - Trámites y requisitos
   - Turnos disponibles
   - Alertas (si hay)
   - Boletería para eventos

3. **Escalamiento:** En `.env` o variables de entorno:
   ```
   ESCALAMIENTO_WHATSAPP=57XXXXXXXXX
   ```

4. **Reporte analítico:**
   ```bash
   python manage.py reporte_analitico --dias 7
   ```
