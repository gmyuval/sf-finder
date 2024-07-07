import time
import requests
import json
from typing import Dict


def find_in_all_branches():
    inv_check_url = 'https://spinventoryapp.super-pharm.co.il/api/InventoryCheck/CheckInventory'
    req_body = ('{{"BranchNumber":{branch_num},'
                '"ProductIds":'
                '["6c95eb2a-ec6f-4b4f-b08e-9befcd3334f9", '
                '"c7439982-7dfa-4614-bcf1-cccbf842e68d", '
                '"9ff665d2-4207-4144-9930-a00f057d4cf4"]}}')
    headers = {'Content-Type': 'application/json'}
    with open('./sfBranchCodes') as f:
        branches: Dict[str, Dict[str, str]] = json.load(f)
    with open('./concertaIds.json') as f:
        ids = json.load(f)
    found = {med_id: [] for med_id in ids}
    for i in branches.keys():
        r = requests.post(inv_check_url, headers=headers, data=req_body)
        try:
            r.raise_for_status()
        except Exception as e:
            print(f'Got server error {e}')
            time.sleep(10)
            continue
        for result in r.json():
            if result['availableInStock'] > 0:
                found[result['productId']].append(result['branchNumber'])
        time.sleep(1)
    return found
