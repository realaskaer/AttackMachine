from modules import Minter, Logger, RequestClient, Client
from config import HYPERCOMIC_ABI
from modules.interfaces import SoftwareException
from utils.tools import helper, gas_checker


class HyperComic(Minter, Logger, RequestClient):
    def __init__(self, client: Client):
        self.client = client
        Logger.__init__(self)
        RequestClient.__init__(self, client)

    async def get_tx_data(self, nft_id: int):
        url = f'https://play.hypercomic.io/Claim/actionZK/conditionsCheck2'

        nonce = 0
        address = self.client.address.lower()

        payload = f'trancnt={nonce}&walletgbn=Metamask&wallet={address}&nftNumber={nft_id}'

        headers = {
            "authority": "play.hypercomic.io",
            "method": "POST",
            "path": "/Claim/actionZK/conditionsCheck2",
            "scheme": "https",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
            #"Content-Length": "92",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://zk24.hypercomic.io",
            "Referer": "https://zk24.hypercomic.io/",
            "Sec-Ch-Ua": '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "Windows",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

        response = await self.client.session.post(url=url, headers=headers, data=payload)
        if response.status == 200:
            return await response.text()
        raise SoftwareException('Bad response from HyperComic API')

    @helper
    @gas_checker
    async def mint(self):

        self.logger_msg(*self.client.acc_info, msg=f'Claim zkList Pass on HyperComic')

        signature = await self.get_tx_data(14)

        if signature != 'notEnough':

            contract_address = '0x1A640bF545E04416Df6FfA2f9Cc4813003E52649'
            amount_in_wei = self.client.to_wei(0.00013)
            claim_contract = self.client.get_contract(contract_address, HYPERCOMIC_ABI)

            tx_data = claim_contract.encodeABI(
                fn_name='mint',
                args=[
                    self.client.w3.to_bytes(hexstr=signature.strip())
                ]
            )

            transaction = await self.client.prepare_transaction() | {
                'to': claim_contract.address,
                'data': tx_data,
                'value': amount_in_wei
            }

            tx_hash = await self.client.send_transaction(transaction, need_hash=True)

            url = 'https://play.hypercomic.io/Claim/actionZK/request'

            payload = f'trancnt=0&walletgbn=Metamask&wallet={self.client.address}&hash={tx_hash}&nftNumber=14'

            headers = {
                "accept": "*/*",
                "accept-language": "de-DE,de;q=0.9",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Sec-Ch-Ua": '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "referrer": "https://zk24.hypercomic.io/",
                "referrerPolicy": "strict-origin-when-cross-origin",
                "method": "POST",
                "mode": "cors",
                "credentials": "omit"
            }

            self.logger_msg(*self.client.acc_info, msg=f'Confirming claim on HyperComic...')

            response = await self.client.session.post(url=url, headers=headers, data=payload)
            if response.status == 200:
                data = await response.text()
                if data == 'success':
                    self.logger_msg(*self.client.acc_info, msg=f'Confirmed claim on HyperComic', type_msg='success')
                    return True
            raise SoftwareException('Bad response from HyperComic API')
        self.logger_msg(*self.client.acc_info, msg=f'Account is not eligible to claim zkList Pass', type_msg='warning')
        return True
