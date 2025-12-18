# Integración con Workbench de Gemini

## 🔧 ¿Qué es Workbench?

Google AI Studio (anteriormente Workbench) es una interfaz web para:
- Probar prompts de Gemini
- Ajustar parámetros de generación
- Crear prompts estructurados
- Exportar configuraciones a código

## 🌐 Acceso a Workbench

URL: https://aistudio.google.com/

## 📝 Casos de Uso con el Chatbot

### 1. Diseñar Prompts Personalizados

#### En Workbench:

1. Ve a https://aistudio.google.com/
2. Selecciona "Freeform prompt"
3. Escribe tu prompt personalizado:

```
Eres un asistente virtual especializado en [TU NEGOCIO].

Características:
- Conoces todos los productos/servicios de [TU EMPRESA]
- Eres experto en [TU INDUSTRIA]
- Respondes consultas sobre [TUS SERVICIOS]

Contexto de conversación:
{context}

Pregunta del cliente:
{message}

Responde de forma profesional y útil:
```

4. Prueba con diferentes mensajes
5. Ajusta los parámetros:
   - **Temperature**: 0.7 (más creativo) o 0.3 (más preciso)
   - **Top-K**: 40 (variedad de respuestas)
   - **Top-P**: 0.95 (coherencia)
   - **Max output tokens**: 1024

#### En tu Código:

Abre `chatbot/services/gemini_service.py` y modifica el prompt:

```python
def get_response(self, message, context=None):
    system_prompt = """Eres un asistente virtual especializado en [TU NEGOCIO].

Características:
- Conoces todos los productos/servicios de [TU EMPRESA]
- Eres experto en [TU INDUSTRIA]
- Respondes consultas sobre [TUS SERVICIOS]

Contexto de conversación:
{context}

Pregunta del cliente:
{message}

Responde de forma profesional y útil:"""
    
    # ... resto del código
```

### 2. Crear Prompts Estructurados

#### En Workbench:

1. Selecciona "Structured prompt"
2. Define campos de entrada:
   - `customer_name`: Nombre del cliente
   - `question`: Pregunta
   - `product_info`: Información del producto

3. Diseña el prompt:
```
Hola {customer_name},

Sobre tu consulta: {question}

Información del producto:
{product_info}

Te recomiendo:
```

#### En tu Código:

```python
# En gemini_service.py
def get_structured_response(self, customer_name, question, product_info):
    prompt = f"""Hola {customer_name},

Sobre tu consulta: {question}

Información del producto:
{product_info}

Te recomiendo:"""
    
    response = self.model.generate_content(prompt)
    return response.text
```

### 3. Chat Multi-turno con Historial

#### En Workbench:

1. Selecciona "Chat prompt"
2. Mantén conversaciones de prueba
3. Observa cómo el modelo mantiene contexto

#### En tu Código (ya implementado):

```python
# Ya está en gemini_service.py
def get_response_with_history(self, messages_history):
    chat = self.model.start_chat(history=[])
    
    for msg in messages_history[:-1]:
        if msg['role'] == 'user':
            chat.send_message(msg['content'])
    
    last_message = messages_history[-1]['content']
    response = chat.send_message(last_message)
    return response.text
```

### 4. Fine-tuning de Parámetros

#### Configuración Recomendada por Uso:

**Para Atención al Cliente (Preciso y Profesional):**
```python
self.generation_config = {
    "temperature": 0.3,      # Más determinístico
    "top_p": 0.8,            # Menos aleatorio
    "top_k": 20,             # Respuestas más enfocadas
    "max_output_tokens": 512,
}
```

**Para Conversaciones Casuales (Creativo y Amigable):**
```python
self.generation_config = {
    "temperature": 0.9,      # Más creativo
    "top_p": 0.95,           # Más variedad
    "top_k": 50,             # Mayor diversidad
    "max_output_tokens": 1024,
}
```

**Para Soporte Técnico (Balance):**
```python
self.generation_config = {
    "temperature": 0.5,      # Balance
    "top_p": 0.9,            # Moderado
    "top_k": 40,             # Standard
    "max_output_tokens": 2048,  # Respuestas detalladas
}
```

## 🎯 Casos de Uso Específicos

### Caso 1: Chatbot de E-commerce

#### Prompt en Workbench:
```
Eres un asistente de ventas para [TIENDA ONLINE].

Base de conocimiento:
- Catálogo: {catalog_data}
- Políticas de envío: {shipping_info}
- Métodos de pago: {payment_methods}

Cliente pregunta: {customer_question}

Responde ayudando en:
1. Búsqueda de productos
2. Información de envíos
3. Proceso de compra
4. Seguimiento de pedidos

Respuesta:
```

#### En el código:
```python
# Agregar en views.py
def process_message(message_data, value):
    # ... código existente ...
    
    if 'catalogo' in content.lower() or 'producto' in content.lower():
        # Buscar en base de datos de productos
        products = get_matching_products(content)
        context += f"\nProductos disponibles: {products}"
    
    response_text = gemini_service.get_response(content, context)
```

### Caso 2: Soporte Técnico

#### Prompt en Workbench:
```
Eres un especialista en soporte técnico de [EMPRESA].

Problema reportado: {issue_description}
Categoría: {category}
Prioridad: {priority}

Pasos para resolver:
1. Identificar el problema
2. Sugerir solución paso a paso
3. Ofrecer contacto con humano si es complejo

Respuesta de soporte:
```

### Caso 3: Reservas y Citas

#### Prompt en Workbench:
```
Eres un asistente para reservas de [NEGOCIO].

Disponibilidad actual:
{available_slots}

Cliente solicita: {request}

Ofrece opciones disponibles y confirma la reserva.
Incluye:
- Fecha y hora
- Nombre del cliente
- Servicio solicitado
- Precio (si aplica)

Respuesta:
```

## 🔄 Workflow Completo: Workbench → Código

### Paso 1: Diseñar en Workbench
1. Abre AI Studio
2. Crea tu prompt
3. Prueba con varios casos
4. Ajusta parámetros
5. Copia el prompt final

### Paso 2: Exportar Configuración
```python
# Copiar de Workbench "Get code" → Python
model = genai.GenerativeModel(
    model_name='gemini-pro',
    generation_config={
        'temperature': 0.7,
        'top_p': 0.95,
        'top_k': 40,
        'max_output_tokens': 1024,
    }
)
```

### Paso 3: Integrar al Bot

```python
# En chatbot/services/gemini_service.py

class GeminiService:
    def __init__(self):
        # ... código existente ...
        
        # Configuración desde Workbench
        self.generation_config = {
            "temperature": 0.7,  # Del experimento en Workbench
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
    
    def get_custom_response(self, message, custom_context):
        """Prompt personalizado desde Workbench"""
        
        # Prompt diseñado en Workbench
        prompt = f"""[TU PROMPT DE WORKBENCH]
        
Contexto: {custom_context}
Usuario: {message}

Respuesta:"""
        
        response = self.model.generate_content(prompt)
        return response.text
```

### Paso 4: Probar Localmente
```bash
python manage.py test_bot
```

### Paso 5: Deploy
```bash
git add .
git commit -m "Updated Gemini prompts from Workbench"
git push
```

## 🎨 Ejemplos de Prompts Listos para Usar

### Prompt 1: Asistente Multilingüe
```
Eres un asistente que responde en el mismo idioma que el usuario.

Idioma detectado: {detected_language}
Mensaje: {message}

Responde en {detected_language} de forma natural y útil:
```

### Prompt 2: Con Emojis y Personalidad
```
Eres un asistente amigable y cercano.

Usa emojis cuando sea apropiado 😊
Sé conversacional y empático
Ayuda con entusiasmo

Usuario dice: {message}

Tu respuesta amigable:
```

### Prompt 3: Formato Estructurado
```
Analiza la consulta y responde en formato:

RESUMEN: [Resumen en una línea]

RESPUESTA DETALLADA:
[Explicación completa]

PRÓXIMOS PASOS:
1. [Paso 1]
2. [Paso 2]

¿NECESITAS MÁS AYUDA?: [Pregunta de seguimiento]

Consulta del usuario: {message}
```

## 🔗 Integración Avanzada

### Combinar Workbench con Base de Datos

```python
# En views.py
def process_message(message_data, value):
    # Obtener datos relevantes
    user_data = get_user_info(from_number)
    order_history = get_order_history(from_number)
    
    # Construir contexto enriquecido
    enriched_context = f"""
Información del cliente:
- Nombre: {user_data.name}
- Cliente desde: {user_data.joined_date}
- Pedidos previos: {len(order_history)}

Historial de conversación:
{conversation_context}
"""
    
    # Usar prompt de Workbench con contexto
    response = gemini_service.get_response(content, enriched_context)
```

## 📊 Monitoreo de Calidad

### Agregar Logging de Prompts

```python
# En gemini_service.py
import json

def get_response(self, message, context=None):
    prompt = self.build_prompt(message, context)
    
    # Guardar para análisis
    with open('prompts_log.json', 'a') as f:
        json.dump({
            'timestamp': str(timezone.now()),
            'prompt': prompt,
            'message': message,
            'context': context
        }, f)
    
    response = self.model.generate_content(prompt)
    return response.text
```

## 🎓 Mejores Prácticas

1. **Siempre prueba en Workbench primero**
2. **Usa ejemplos concretos en tus prompts**
3. **Itera basándote en respuestas reales**
4. **Documenta tus mejores prompts**
5. **Versiona tus cambios de prompts**

## 📚 Recursos Adicionales

- **AI Studio**: https://aistudio.google.com/
- **Guía de Prompts**: https://ai.google.dev/docs/prompt_best_practices
- **Modelos disponibles**: https://ai.google.dev/models/gemini

---

**Con Workbench puedes diseñar, probar y perfeccionar tus prompts antes de implementarlos en producción.**
