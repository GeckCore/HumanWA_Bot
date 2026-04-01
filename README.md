# HumanBot: Comunicación Automatizada con IA Local

Este proyecto permite automatizar respuestas de WhatsApp utilizando modelos de lenguaje (LLM) locales a través de **Ollama**. Está diseñado para mantener conversaciones naturales y humanas, gestionando diferentes perfiles de contacto (abuelos, padres, tíos, etc.) de forma independiente.

## 🚀 Requisitos Previos

Antes de empezar, asegúrate de tener instalado:
* **Node.js** (v18 o superior)
* **Python** (3.10 o superior)
* **Ollama** (Descárgalo en [ollama.com](https://ollama.com))
* **FFmpeg** (Necesario para que Whisper procese audios)

## 🛠️ Instalación

### 1. Modelos de IA (Ollama)
Para este proyecto se recomienda **qwen2.5:14b** por su excelente capacidad para seguir roles y mantener el hilo de la conversación en español.

```bash
# Instalar el modelo recomendado
ollama pull qwen2.5:14b

# (Opcional) Si tienes menos de 12GB de RAM, puedes usar:
ollama pull llama3.1
```

### 2. Dependencias de Node.js (WhatsApp Bridge)
En la carpeta raíz, instala las librerías necesarias para la conexión con WhatsApp:
```bash
npm install @whiskeysockets/baileys qrcode-terminal axios pino
```

### 3. Dependencias de Python (Cerebro IA)
Instala las librerías para el servidor Flask y el procesamiento de voz:
```bash
pip install flask requests openai-whisper torch
```

## ⚙️ Configuración y Uso

### Paso 1: Configurar Contactos
En el archivo `bot.py`, localiza el diccionario `CONTACTOS_CONFIG`. Debes añadir el ID interno del contacto y el parentesco:

```python
CONTACTOS_CONFIG = {
    "8061888557221": "Abuelo",
    "5492613619545": "Tío"
}
```
*Nota: Si no conoces el ID interno, ejecuta el bot y revisa los logs de la consola de Python cuando recibas un mensaje; el ID bloqueado aparecerá allí.*

### Paso 2: Ejecución
Debes tener dos terminales abiertas:

1.  **Terminal 1 (IA):** `python bot.py`
2.  **Terminal 2 (WhatsApp):** `node index.js`

Al ejecutar `index.js` por primera vez, aparecerá un **código QR**. Escanéalo desde tu WhatsApp en **Dispositivos vinculados > Vincular un dispositivo**.

## 🧠 Propósito del Proyecto
Este bot nace de la necesidad de mitigar la soledad en personas mayores o familiares con los que, por diversas circunstancias, no mantenemos una comunicación fluida. Funciona como un puente de "mentira piadosa" para asegurar que siempre reciban una respuesta interesada, afectuosa y humana, evitando que se sientan ignorados.

## ⚖️ Análisis Ético (Riesgos y Beneficios)

### Beneficios
* **Acompañamiento emocional:** Evita la sensación de abandono en personas vulnerables.
* **Disponibilidad 24/7:** La IA siempre tiene tiempo para escuchar y responder de forma calmada.
* **Reducción de arrepentimiento:** Actúa como un soporte para quienes no pueden gestionar la carga social en momentos críticos.

### Riesgos
* **Alucinaciones:** Como toda IA, el modelo puede inventar datos biográficos o prometer visitas que no ocurrirán.
* **Impacto por descubrimiento:** Si el familiar descubre que habla con una máquina, el daño emocional puede ser superior a la falta de respuesta inicial.
* **Privacidad:** Aunque el modelo es **local** y los datos no salen de tu PC, el historial se almacena en archivos JSON (`historial_contactos.json`).

## ⚠️ Advertencia Técnica
Este bot utiliza **Baileys**, una librería no oficial de WhatsApp. Existe un riesgo mínimo de baneo si se usa para spam masivo. Úsalo con moderación y solo con los contactos configurados.
```

### Notas adicionales para ti:
1.  **Privacidad total:** Como estás usando **Ollama (qwen2.5:14b)**, todas las conversaciones se procesan en tu propia tarjeta gráfica/procesador. Nada se envía a la nube.
2.  **Mantenimiento:** Te recomiendo borrar el archivo `historial_contactos.json` cada pocas semanas si notas que la IA empieza a confundir temas muy antiguos, aunque el código ya limita el contexto a los últimos 25 mensajes para evitarlo.
3.  **Memoria:** Al dedicarle 20GB y usar el modelo de 14B, la calidad de las respuestas será muy superior a lo que viste con Llama 3 de 8B.
