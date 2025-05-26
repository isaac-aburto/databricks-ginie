import requests

space_id = '01f0371abefe1428820302702c9a3fbd'
conversation_id = '01f039e9dd4d172398d8242d0aac7efc'
message_id = '01f039e9dd5811caa6d9806aa6026b82'

url = f'https://dbc-bc1730d4-9722.cloud.databricks.com/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}'

headers = {
    'Authorization': 'Bearer dapi8e27b9a37ebad4152c17c4e2307c116d'
}

response = requests.get(url, headers=headers)
print(response.status_code)
print(response.json())
