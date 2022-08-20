import requests
import pandas as pd
import time

while True:
    try:
        master_file = pd.read_json(requests.get('https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json').text)
        break
    except:
        time.sleep(1)
        continue
