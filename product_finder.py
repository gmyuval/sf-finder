import time
import requests
import json
from typing import Dict, List, Optional
from math import ceil
from datetime import datetime

import asyncio
import aiohttp


def find_in_all_branches(product_ids: List[str] = None) -> Dict[str, List[str]]:
    inv_check_url = 'https://spinventoryapp.super-pharm.co.il/api/InventoryCheck/CheckInventory'
    req_body = '{{"BranchNumber":{branch_num},' + f'"ProductIds":{json.dumps(product_ids)}' + '}}'
    headers = {'Content-Type': 'application/json'}
    with open('resources/sfBranchCodes.json', encoding='utf-8') as f:
        branches: Dict[str, Dict[str, str]] = json.load(f)
    with open('resources/concertaIds.json', encoding='utf-8') as f:
        ids = json.load(f)
    found = {med_id: [] for med_id in ids}
    for i in branches.keys():
        r = requests.post(inv_check_url, headers=headers, data=req_body.format(branch_num=i))
        try:
            r.raise_for_status()
        except Exception as e:
            print(f'Got server error {e}')
            time.sleep(10)
            continue
        for result in r.json()['inventoryData']['items']:
            if result['availableInStock'] > 0:
                found[result['productId']].append(result['branchNumber'])
        time.sleep(1)
    return found


class InventoryFinder:
    INVENTORY_CHECK_URL = 'https://spinventoryapp.super-pharm.co.il/api/InventoryCheck/CheckInventory'
    HEADERS = {'Content-Type': 'application/json'}

    def __init__(self):
        with open('resources/sfBranchCodes.json', encoding='utf-8') as f:
            self.branches: Dict[str, Dict[str, str]] = json.load(f)
        with open('resources/concertaIds.json', encoding='utf-8') as f:
            self.product_details = json.load(f)
        self.product_ids: List[str] = list(self.product_details.keys())
        self.branch_ids: List[str] = list(self.branches.keys())
        self.request_body = '{{"BranchNumber":{branch_num},' + f'"ProductIds":{json.dumps([f"{product_id}" for product_id in self.product_ids])}' + '}}'
        self.branches_with_inventory = {med_id: [] for med_id in self.product_ids}
        self.failed_branches = []

    @staticmethod
    def chunk_into_n(lst: List[str], n: int) -> List[List[str]]:
        size = ceil(len(lst) / n)
        return list(
            map(lambda x: lst[x * size:x * size + size],
                list(range(n)))
        )

    async def get_inventory_in_branches(self, branch_list: List[str]):
        async with aiohttp.ClientSession() as session:
            for branch in branch_list:
                async with session.post(self.INVENTORY_CHECK_URL, headers=self.HEADERS, data=self.request_body.format(branch_num=branch)) as response:
                    if not response.ok:
                        print(f'got response {response.status} from server on branch {branch}')
                        self.failed_branches.append(branch)
                        continue
                    for result in (await response.json())['inventoryData']['items']:
                        if result['availableInStock'] > 0:
                            self.branches_with_inventory[result['productId']].append(result['branchNumber'])
                # await asyncio.sleep(1.5)

    async def get_inventory(self):
        batches = self.chunk_into_n(self.branch_ids, 6)
        for i, batch in enumerate(batches):
            print(f'{datetime.now().time()}: starting batch {i+1} of {len(batches)}')
            chunks = self.chunk_into_n(batch, 3)
            tasks = [self.get_inventory_in_branches(chunk) for chunk in chunks]
            await asyncio.gather(*tasks)
            print(f'{datetime.now().time()}: finished batch {i+1} of {len(batches)} sleeping for 30 seconds')
            await asyncio.sleep(30)
        return self.branches_with_inventory

    def check_inventory_in_branch(self, branch_id: str) -> Optional[List[str]]:
        req_body = '{{"BranchNumber":{branch_num},' + f'"ProductIds":{json.dumps(self.product_ids)}' + '}}'
        r = requests.post(self.INVENTORY_CHECK_URL, headers=self.HEADERS, data=req_body.format(branch_num=branch_id))
        if not r.ok:
            print(f'got response {r.status_code} from server on branch {branch_id}')
            self.failed_branches.append(branch_id)
            return None
        return [result['productId'] for result in r.json()['inventoryData']['items'] if result['availableInStock'] > 0]

    def find_in_all_branches(self) -> Dict[str, List[str]]:
        """
        Find all branches with inventory for the given product ids

        :return: Dict with product ids as keys and list of branch numbers as values
        """
        self.branches_with_inventory = {key: [] for key in self.branches_with_inventory}
        for branch_id in self.branch_ids:
            branch_result = self.check_inventory_in_branch(branch_id)
            for product_id in branch_result:
                self.branches_with_inventory[product_id].append(branch_id)
            time.sleep(1)
        return self.branches_with_inventory
