# genie_chatbot.py
import requests
import time
import json

# Configuración
BASE_URL = "https://dbc-bc1730d4-9722.cloud.databricks.com"
API_TOKEN = "dapi8e27b9a37ebad4152c17c4e2307c116d"
SPACE_ID = "01f0371abefe1428820302702c9a3fbd"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}


def start_conversation(prompt):
    """Envía una pregunta a Genie y devuelve IDs necesarios."""
    url = f"{BASE_URL}/api/2.0/genie/spaces/{SPACE_ID}/start-conversation"
    data = {"content": prompt}
    response = requests.post(url, headers=HEADERS, json=data)
    response.raise_for_status()
    res_json = response.json()

    message_id = res_json["message_id"]
    conversation_id = res_json["conversation_id"]

    return conversation_id, message_id

def get_response(space_id, conversation_id, message_id):
    # Esperar hasta que se complete
    try:
        message = wait_for_completion(space_id, conversation_id, message_id)
    except TimeoutError as e:
        return str(e)

    # Si falló
    if message["status"] == "FAILED":
        return "La solicitud falló. Intenta nuevamente o revisa el prompt."

    # Si no hay adjuntos (respuesta en texto plano, por ejemplo)
    if "attachments" not in message or not message["attachments"]:
        return f"Respuesta simple:\n{message.get('content', '[Sin contenido]')}"

    # Obtener attachment_id
    attachment_id = message["attachments"][0]["attachment_id"]

    # Obtener resultados
    result_url = f'{BASE_URL}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/attachments/{attachment_id}/query-result'
    result_response = requests.get(result_url, headers=HEADERS)
    result_response.raise_for_status()
    result_data = result_response.json()

    # Si los datos vienen dentro de statement_response
    if "statement_response" in result_data:
        result_data = result_data["statement_response"]

    try:
        columns = result_data["manifest"]["schema"]["columns"]
        rows = result_data["result"]["data_array"]
    except KeyError:
        return f"Respuesta cruda (no estructurada):\n{result_data}"

    headers = [col["name"] for col in columns]
    table = [headers] + rows
    formatted = "\n".join(["\t".join(map(str, row)) for row in table])
    return f"Resultados:\n{formatted}"

def wait_for_completion(space_id, conversation_id, message_id, max_retries=20, wait_seconds=2):
    """Espera hasta que el mensaje tenga un estado FINAL"""
    url = f'{BASE_URL}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}'

    for _ in range(max_retries):
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        message = response.json()
        
        status = message.get("status")
        print(f"Estado actual: {status}") 
        
        if status in ["COMPLETED", "FAILED"]:
            return message

        time.sleep(wait_seconds)

    raise TimeoutError("El mensaje no se completó en el tiempo esperado.")

def ask_genie(prompt):
    """Función general para interactuar con Genie"""
    conversation_id, message_id = start_conversation(prompt)
    return get_response(SPACE_ID, conversation_id, message_id)
