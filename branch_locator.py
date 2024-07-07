from typing import Dict

import requests


def get_branches_by_code() -> Dict[int, Dict[str, str]]:
    branches_url = ('https://shop.super-pharm.co.il/branches/'
                    'filter?q=&page={page_num}'
                    '&buildFacets=true&selectedCity=&clinic=&service=&brand=&branch=&ignoreDistanceLimit=true')
    wanted_keys = ['branchCode', 'branchCity', 'branchName']
    num_pages = requests.get(branches_url.format(page_num=0)).json()['pagination']['numberOfPages']
    branches_list = []
    for i in range(num_pages):
        r = requests.get(branches_url.format(page_num=i))
        branches_list.extend([{key: store[key] for key in wanted_keys} for store in r.json()['storeList']])
    branches_by_code = {branch['branchCode']: {
        'branchName': branch['branchName'],
        'branchCity': branch['branchCity']
    } for branch in branches_list}
    return branches_by_code
