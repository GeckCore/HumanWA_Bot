import os
import json
import random
import requests
import base64
import tempfile
import whisper
from flask import Flask, request, jsonify

# ── CONFIGURACIÓN DE CONTACTOS Y RELACIONES
# Añade aquí los IDs/números y define qué son para ti.
CONTACTOS_CONFIG = {
    "34000000000": "Abuelo",
    "540000000": "Tío",
    "34600000000": "Padre"
}

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
MODELO_LLM      = "qwen2.5:14b" 
ARCHIVO_CHATS   = "historial_contactos.json"

app = Flask(__name__)

# ─────────────────────────────────────────────
# MOTOR DE AUDIO (WHISPER)
# ─────────────────────────────────────────────
STT_MODEL = None

def transcribir_audio(base64_audio: str) -> str:
    global STT_MODEL
    if STT_MODEL is None:
        print("[INFO] Cargando modelo Whisper...")
        STT_MODEL = whisper.load_model("small")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
            tmp.write(base64.b64decode(base64_audio))
            tmp_path = tmp.name
        
        resultado = STT_MODEL.transcribe(tmp_path, language="es")
        texto_final = resultado["text"].strip()
        os.remove(tmp_path)
        return texto_final
    except Exception as e:
        print(f"[ERROR Audio] {e}")
        return ""

# ─────────────────────────────────────────────
# GESTIÓN DE HISTORIAL
# ─────────────────────────────────────────────
def cargar_historial():
    if os.path.exists(ARCHIVO_CHATS):
        try:
            with open(ARCHIVO_CHATS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def guardar_historial(ruta, datos):
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)

historial = cargar_historial()

# ─────────────────────────────────────────────
# GENERADOR QWEN
# ─────────────────────────────────────────────
def limpiar_respuesta(texto: str) -> str:
    # Elimina muletillas de IA y puntuación excesiva
    texto = texto.replace("¿", "").replace("¡", "")
    if texto.endswith("."):
        texto = texto[:-1]
    return texto.strip()

def generar_respuesta(contacto_id: str, parentesco: str, mensaje: str) -> str:
    instrucciones = (
        f"Eres un joven de 17 años de España. Estás chateando por WhatsApp con tu {parentesco}. "
        "REGLAS DE COMPORTAMIENTO:\n"
        f"1. Eres humano, no una IA. Mantén una conversación natural con tu {parentesco}.\n"
        "2. Respuestas cortas y directas, como un adolescente real. Usa lenguaje coloquial de España.\n"
        "3. No des sermones ni uses frases hechas de asistente. Sé auténtico.\n"
        "4. Usa el contexto del chat para responder con lógica a lo que te acaban de decir."
    )

    messages = [{"role": "system", "content": instrucciones}]
    
    # Contexto independiente por cada contacto
    turns = historial.get(contacto_id, [])
    for t in turns[-10:]: # Qwen aguanta bien contextos largos
        messages.append({"role": t["role"], "content": t["content"]})
        
    messages.append({"role": "user", "content": mensaje})
    
    try:
        r = requests.post(OLLAMA_CHAT_URL, json={
            "model":  MODELO_LLM,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.65,
                "top_p": 0.9
            }
        }, timeout=60)
        
        r.raise_for_status() 
        respuesta_raw = r.json().get("message", {}).get("content", "").strip()
        
        if not respuesta_raw:
            raise ValueError("Sin respuesta del modelo.")

        respuesta = limpiar_respuesta(respuesta_raw)

        # Guardar en el historial específico de este ID
        if contacto_id not in historial:
            historial[contacto_id] = []
            
        historial[contacto_id].append({"role": "user", "content": mensaje})
        historial[contacto_id].append({"role": "assistant", "content": respuesta})
        
        if len(historial[contacto_id]) > 25:
            historial[contacto_id] = historial[contacto_id][-25:]
            
        guardar_historial(ARCHIVO_CHATS, historial)
        return respuesta

    except Exception as e:
        print(f"[ERROR OLLAMA] {e}")
        return "Luego te escribo que no tengo mucha batería."

def delay_humano(msg_in: str, msg_out: str) -> int:
    ms = len(msg_in.split()) * 150 + len(msg_out) * 100 + random.randint(1000, 3000)
    return max(2000, min(ms, 12000))

# ─────────────────────────────────────────────
# WEBHOOK FLASK
# ─────────────────────────────────────────────
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    remitente_raw = data.get("remitente", "")
    remitente_id  = remitente_raw.split('@')[0] 
    
    mensaje   = data.get("mensaje", "")
    audio_b64 = data.get("audio_b64", "")
    es_mio    = data.get("es_mio", False)

    # Verificamos si el remitente está en nuestra configuración
    parentesco = CONTACTOS_CONFIG.get(remitente_id)

    if not parentesco and not es_mio:
        return jsonify({"respuesta": "", "error": "No autorizado"}), 403

    if audio_b64:
        texto_audio = transcribir_audio(audio_b64)
        if texto_audio: mensaje = texto_audio

    if not mensaje:
        return jsonify({"respuesta": "", "delay_ms": 0}), 400

    if es_mio:
        return jsonify({"respuesta": "Configuración activa.", "delay_ms": 200})

    # Generamos respuesta pasando el parentesco específico
    respuesta = generar_respuesta(remitente_id, parentesco, mensaje)
    return jsonify({
        "respuesta": respuesta, 
        "delay_ms": delay_humano(mensaje, respuesta)
    })

if __name__ == '__main__':
    print(f"Servidor listo. Modelo: {MODELO_LLM}")
    app.run(host='0.0.0.0', port=5000)
