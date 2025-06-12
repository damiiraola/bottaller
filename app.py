# -*- coding: utf-8 -*-
# pip install Flask google-generativeai
# (Este comando se ejecutaría en el servidor donde alojemos el bot)

import re
import json
import google.generativelanguage as genai
from flask import Flask, request, jsonify

# --------------------------------------------------------------------------
# --- Configuración del Servidor y la API de Gemini ---
# --------------------------------------------------------------------------

# Creamos la aplicación del servidor web
app = Flask(__name__)

# Tu API Key de Google AI Studio
API_KEY = 'AIzaSyBgLy8n402kltv_4PZIgpbPn6SS92uFF_8' 

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("[Estado] Conexión con la API de Gemini configurada.")
except Exception as e:
    print(f"Error configurando la API de Gemini: {e}")
    model = None

# --------------------------------------------------------------------------
# --- Las funciones que ya teníamos (Cerebro del Bot y Consulta a BD) ---
# --------------------------------------------------------------------------

def consultar_estado_reparacion_api(numero_orden):
    """Simula la búsqueda en la base de datos del taller."""
    print(f"\n[Sistema] Buscando orden '{numero_orden}'...")
    base_de_datos_ficticia = {
        "12345": {"estado": "Listo para retirar", "costo": "15000 ARS"},
        "54321": {"estado": "En diagnóstico"},
        "98765": {"estado": "Esperando repuestos", "detalle": "Pantalla nueva"},
    }
    return base_de_datos_ficticia.get(numero_orden)

def entender_intencion_con_gemini(mensaje):
    """Llama a la API de Gemini para entender la intención y extraer datos."""
    if not model:
        return {"intent": "error_api", "entities": {}}
    
    prompt_instrucciones = f"""
    Eres un asistente virtual para un taller de reparaciones. Tu tarea es clasificar el mensaje de un cliente.
    Responde SIEMPRE en formato JSON con la clave "intent" y opcionalmente "entities".
    Intenciones posibles: "saludar", "consultar_estado", "proporcionar_numero_orden", "agradecer", "despedirse", "no_entendido".
    Si la intención es "proporcionar_numero_orden", extrae el número en "entities".
    
    Cliente: "{mensaje}"
    Tu respuesta:
    """
    try:
        response = model.generate_content(prompt_instrucciones)
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_response_text)
    except Exception as e:
        print(f"[Error] No se pudo procesar la respuesta de Gemini: {e}")
        return {"intent": "no_entendido", "entities": {}}

def procesar_mensaje_cliente(mensaje):
    """Procesa el mensaje del cliente y devuelve una respuesta de texto."""
    intencion = entender_intencion_con_gemini(mensaje)
    nombre_intencion = intencion.get("intent", "no_entendido")
    
    print(f"[Cerebro del Bot] Intención detectada: {nombre_intencion}")
    
    # La lógica es la misma que ya teníamos...
    if nombre_intencion == "saludar":
        return "¡Hola! Soy tu asistente virtual potenciado por IA. ¿En qué te puedo ayudar?"
    elif nombre_intencion == "consultar_estado":
        return "¡Claro! Para eso necesito el número de orden, por favor."
    elif nombre_intencion == "proporcionar_numero_orden":
        entities = intencion.get("entities", {})
        numero_orden = entities.get("numero_orden")
        if numero_orden:
            datos = consultar_estado_reparacion_api(numero_orden)
            if datos:
                return f"La orden {numero_orden} figura como: **{datos['estado']}**."
            else:
                return "Lo siento, no pude encontrar esa orden. ¿Podrías verificar el número?"
        else:
            return "No pude identificar el número de orden. ¿Puedes escribirlo de nuevo?"
    # ... (resto de las intenciones)
    else:
        return "Disculpa, no te he entendido bien. Puedes preguntarme por el estado de una reparación."

# --------------------------------------------------------------------------
# --- NUEVO: El Webhook que escuchará a WhatsApp ---
# --------------------------------------------------------------------------

@app.route('/whatsapp', methods=['POST'])
def webhook_whatsapp():
    """
    Este es el corazón del servidor. Escucha los mensajes que llegan de WhatsApp.
    """
    # Extraemos el mensaje del cuerpo de la petición que nos envía WhatsApp/Twilio
    # El formato exacto puede variar según el proveedor (Twilio, Meta, etc.)
    body = request.get_json()
    mensaje_cliente = body.get('Body', 'No hay mensaje') # Ejemplo para Twilio
    numero_cliente = body.get('From', 'Desconocido')
    
    print(f"Mensaje recibido de {numero_cliente}: '{mensaje_cliente}'")
    
    # 2. Procesamos el mensaje con la lógica que ya tenemos
    respuesta_bot = procesar_mensaje_cliente(mensaje_cliente)
    
    print(f"Respuesta generada para {numero_cliente}: '{respuesta_bot}'")
    
    # 3. Devolvemos la respuesta en el formato que espera el proveedor de WhatsApp
    # Esto es una simulación de la respuesta a Twilio (TwiML)
    return f"""
    <Response>
        <Message>{respuesta_bot}</Message>
    </Response>
    """

# --- Para ejecutar el servidor (en un entorno de producción se usaría algo como Gunicorn)
if __name__ == '__main__':
    # El host='0.0.0.0' hace que sea accesible desde fuera de tu máquina
    app.run(host='0.0.0.0', port=5000, debug=True)
