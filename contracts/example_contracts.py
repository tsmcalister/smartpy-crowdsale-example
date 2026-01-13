import smartpy as sp
from smartpy.templates import fa2_lib as fa2
from contracts.rng_utils import rng_utils

# Main template for FA2 contracts
main = fa2.main


@sp.module
def my_module():
    import main
    import rng_utils

    class NFTContract(
        main.Admin,
        main.Nft,
        main.OnchainviewBalanceOf,
    ):
        def __init__(self, admin_address, contract_metadata, ledger, token_metadata):
            main.OnchainviewBalanceOf.__init__(self)
            main.Nft.__init__(self, contract_metadata, ledger, token_metadata)
            main.Admin.__init__(self, admin_address)

        @sp.entrypoint
        def mint(self, params):
            assert sp.sender == self.data.administrator
            assert not self.data.ledger.contains(params.token_id), "TOKEN_MINTED"
            sp.cast(params, sp.record(target=sp.address, metadata=sp.bytes, token_id=sp.nat))
            self.data.ledger[params.token_id] = params.target
            self.data.token_metadata[params.token_id] = sp.record(
                token_id=params.token_id,
                token_info={
                    "": params.metadata
                }
            )

    class Crowdsale(sp.Contract):
        def __init__(self, admin, nft_contract, rng_oracle, supply):
            self.data.admin = admin
            self.data.nft_contract = nft_contract
            self.data.price = sp.mutez(0)
            self.data.purchase_count = 0
            self.data.rng_oracle = rng_oracle
            self.data.remaining_supply = supply
            self.data.total_supply = supply
            self.data.available_tokens = sp.cast(sp.big_map({}), sp.big_map[sp.nat, sp.record(token_id=sp.nat, metadata=sp.bytes)])
            self.data.pending_purchases = sp.cast(sp.big_map({}), sp.big_map[sp.nat, sp.record(buyer=sp.address, entropy=sp.bytes)])
        
        @sp.entrypoint
        def set_tokens(self, tokens):
            assert sp.sender == self.data.admin, "NONO"
            for token in tokens:
                self.data.available_tokens[token.idx] = token.value
        
        @sp.entrypoint
        def set_supply(self, supply):
            assert sp.sender == self.data.admin, "NONO"
            assert self.data.purchase_count == 0, "ALREADY_STARTED"
            self.data.remaining_supply = supply
            self.data.total_supply = supply        

        @sp.entrypoint
        def set_price(self, price):
            assert sp.sender == self.data.admin, "NONO"
            self.data.price = price

        @sp.entrypoint
        def buy(self, user_entropy):
            assert sp.amount == self.data.price, "INVALID_AMOUNT"
            assert self.data.purchase_count < self.data.total_supply, "SOLD_OUT"
            if sp.amount > sp.mutez(0):
                sp.send(self.data.admin, sp.amount)
            purchase_id = self.data.purchase_count
            self.data.pending_purchases[purchase_id] = sp.record(
                buyer=sp.sender,
                entropy=user_entropy
            )
            self._request_entropy(purchase_id)
            self.data.purchase_count += 1
        
        @sp.entrypoint
        def fulfill_entropy(self, params):
            assert sp.sender == self.data.rng_oracle, "ONLY_ORACLE"
            sp.cast(params, sp.record(request_id=sp.nat, entropy=sp.bytes))
            purchase = self.data.pending_purchases[params.request_id]
            mixed_entropy = sp.sha256(params.entropy + purchase.entropy)
            random_index = rng_utils.draw_uniform(
                sp.record(entropy=mixed_entropy, n=self.data.remaining_supply)
            )
            token = self.data.available_tokens[random_index]
            self._mint(sp.record(
                target=purchase.buyer,
                metadata=token.metadata,
                token_id=token.token_id
            ))
            last_index = sp.as_nat(self.data.remaining_supply - 1)
            self.data.available_tokens[random_index] = self.data.available_tokens[last_index]
            del self.data.available_tokens[last_index]

            self.data.remaining_supply = sp.as_nat(self.data.remaining_supply - 1)
            del self.data.pending_purchases[params.request_id]
        
        @sp.private(with_storage="read-only", with_operations=True)
        def _request_entropy(self, purchase_id):
            contract = sp.contract(sp.nat, self.data.rng_oracle, entrypoint="request_entropy").unwrap_some()
            sp.transfer(
                purchase_id, 
                sp.mutez(0), 
                contract
            )
        
        @sp.private(with_storage="read-only", with_operations=True)
        def _mint(self, params):
            contract = sp.contract(sp.record(target=sp.address, metadata=sp.bytes, token_id=sp.nat), self.data.nft_contract, entrypoint="mint").unwrap_some()
            sp.transfer(params, sp.mutez(0), contract)
    
    class Randomiser(sp.Contract):
        # this is obviously NOT a secure RNG oracle
        # replace with something better in your implementation
        # or not, you're old enough to decide yourself
        # this could be asynchronous instead of calling back immediately
        def __init__(self):
            self.data.last_value = sp.bytes("0x00")

        @sp.entrypoint
        def request_entropy(self, request_id):
            # use sp.now sp.level and last_value to drive some bad entropy
            random_bytes = sp.sha256(sp.pack(sp.pack(sp.record(request_id=request_id, timestamp=sp.now, level=sp.level, last_value=self.data.last_value))))
            self.data.last_value = random_bytes
            contract = sp.contract(sp.record(request_id=sp.nat, entropy=sp.bytes), sp.sender, entrypoint="fulfill_entropy").unwrap_some()
            sp.transfer(
                sp.record(request_id=request_id, entropy=random_bytes), 
                sp.mutez(0), 
                contract
            )


def compile_all(dir):
    @sp.add_test()
    def compile_nft():
        scenario = sp.test_scenario(f"{dir}/my_nft")
        admin = sp.test_account("Admin")
        nft = my_module.NFTContract(
            admin.address, sp.big_map(), {}, []
        )
        scenario += nft


    @sp.add_test()
    def compile_crowdsale():
        scenario = sp.test_scenario(f"{dir}/my_crowdsale")
        admin = sp.test_account("Admin")
        my_crowdsale = my_module.Crowdsale(admin.address, admin.address, admin.address, 0)
        scenario += my_crowdsale

    @sp.add_test()
    def compile_randomiser():
        scenario = sp.test_scenario(f"{dir}/rng_oracle")
        admin = sp.test_account("Admin")
        randomiser = my_module.Randomiser()
        scenario += randomiser