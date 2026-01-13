import os

from dotenv import load_dotenv
load_dotenv()

from pytezos import pytezos, ContractInterface


def load_contract(name):
    contract_path = os.path.join("build", name, "step_001_cont_0_contract.tz")
    return ContractInterface.from_file(contract_path)

def get_first_originated_contract(opg):
    return opg.opg_result['contents'][0]['metadata']['operation_result']['originated_contracts'][0]

if __name__ == "__main__":
    pt = pytezos.using(key=os.environ["TZ_SECRET_KEY"], shell="https://ghostnet.smartpy.io")

    oracle = load_contract("rng_oracle")
    storage = b'initial_value'
    opg = pt.origination(script=oracle.script(initial_storage=storage)).send(min_confirmations=1)
    oracle_contract = get_first_originated_contract(opg)
    print(f"Oracle deployed at: {oracle_contract}")

    nft = load_contract("my_nft")
    storage = {
        "administrator": pt.key.public_key_hash(),
        "metadata": {},
        "operators": {},
        "token_metadata": {},
        "ledger": {},
        "next_token_id": 0,
    }
    opg = pt.origination(script=nft.script(initial_storage=storage)).send(min_confirmations=1)
    nft_contract = get_first_originated_contract(opg)
    print(f"NFT deployed at: {nft_contract}")

    crowdsale = load_contract("my_crowdsale")
    storage = {
        "admin": pt.key.public_key_hash(),
        "nft_contract": nft_contract,
        "price": 0,
        "purchase_count": 0,
        "rng_oracle": oracle_contract,
        "remaining_supply": 100,
        "total_supply": 100,
        "available_tokens": {},
        "pending_purchases": {},
    }
    opg = pt.origination(script=crowdsale.script(initial_storage=storage)).send(min_confirmations=1)
    crowdsale_contract = get_first_originated_contract(opg)
    print(f"Crowdsale deployed at: {crowdsale_contract}")

    print(pt.contract(nft_contract).set_administrator(crowdsale_contract).send(min_confirmations=1).hash())

    tokens = [
        f"ipfs://{i}".encode() for i in range(100)
    ] # could be pre-uploaded ipfs uris

    pt.contract(crowdsale_contract).set_tokens([
        {"idx": i, "value": {"token_id": i, "metadata": tokens[i]}} for i in range(100)
    ]).send(min_confirmations=1)
    print("added tokens")

    pt.contract(crowdsale_contract).set_supply(100).send(min_confirmations=1)
    print("set supply")

    # purchase
    pt.contract(crowdsale_contract).buy("my_entropy".encode()).send(min_confirmations=1)