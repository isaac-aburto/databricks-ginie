#databricks auth login --host https://dbc-bc1730d4-9722.cloud.databricks.com
#dapi8e27b9a37ebad4152c17c4e2307c116d
import requests

url = 'https://dbc-bc1730d4-9722.cloud.databricks.com/api/2.0/genie/spaces/01f0371abefe1428820302702c9a3fbd/start-conversation'

headers = {
    'Authorization': 'Bearer dapi8e27b9a37ebad4152c17c4e2307c116d',
    'Content-Type': 'application/json'
}

data = {
    "content": "Cuál fue la posición del ranking de montos que estaba Metlife en el 2023?"
}

response = requests.post(url, headers=headers, json=data)

print(response.status_code)
print(response.json())