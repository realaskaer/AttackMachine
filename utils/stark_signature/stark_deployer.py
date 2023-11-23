from starknet_py.hash.address import compute_address
from starknet_py.net.signer.stark_curve_signer import KeyPair, StarkCurveSigner
from starknet_py.hash.utils import message_signature
from starknet_py.hash.utils import compute_hash_on_elements
from starknet_py.net.models import AddressRepresentation, StarknetChainId
from starknet_py.net.models.transaction import DeployAccount
from starknet_py.hash.transaction import compute_deploy_account_transaction_hash

from config import BRAAVOS_IMPLEMENTATION_CLASS_HASH_NEW


class BraavosCurveSigner(StarkCurveSigner):
    def __init__(
            self,
            account_address: AddressRepresentation,
            key_pair: KeyPair,
            chain_id: StarknetChainId
    ):
        """
        :param account_address: Address of the account contract.
        :param key_pair: Key pair of the account contract.
        :param chain_id: ChainId of the chain.
        """
        super().__init__(account_address, key_pair, chain_id)

    def _sign_deploy_account_transaction(self, transaction: DeployAccount) -> list[int]:
        contract_address = compute_address(
            salt=transaction.contract_address_salt,
            class_hash=transaction.class_hash,
            constructor_calldata=transaction.constructor_calldata,
            deployer_address=0,
        )
        tx_hash = compute_deploy_account_transaction_hash(
            contract_address=contract_address,
            class_hash=transaction.class_hash,
            constructor_calldata=transaction.constructor_calldata,
            salt=transaction.contract_address_salt,
            max_fee=transaction.max_fee,
            version=transaction.version,
            chain_id=self.chain_id,
            nonce=transaction.nonce,
        )

        tx_hash = compute_hash_on_elements([tx_hash, BRAAVOS_IMPLEMENTATION_CLASS_HASH_NEW, 0, 0, 0, 0, 0, 0, 0])

        r, s = message_signature(msg_hash=tx_hash, priv_key=self.private_key)
        return [r, s, BRAAVOS_IMPLEMENTATION_CLASS_HASH_NEW, 0, 0, 0, 0, 0, 0, 0]
