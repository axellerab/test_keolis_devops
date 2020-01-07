import requests
headers = {'Content-Type': 'application/json'}
input_data = "{\"data\": [" + str([0,0,0,0,0]) + "]}"
requests.post("http://28daeeb2-1f19-4b2e-a190-733793fce857.westeurope.azurecontainer.io/score", input_data, headers=headers).text
