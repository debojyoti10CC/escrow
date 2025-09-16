from algopy import ARC4Contract, String, UInt64, GlobalState, Bytes, arc4

class Escrow(ARC4Contract):
    def __init__(self) -> None:
        self.client = GlobalState(Bytes, key="client", description="Client address")
        self.provider = GlobalState(Bytes, key="provider", description="Provider address")
        self.amount = GlobalState(UInt64, key="amount", description="Escrow amount (microALGO)")
        self.expiry = GlobalState(UInt64, key="expiry", description="Expiry timestamp")
        self.arbiter = GlobalState(Bytes, key="arbiter", description="Arbiter address")
        self.status = GlobalState(String, key="status", description="Escrow status")

    @arc4.abimethod(create="require")
    def create(
        self,
        provider: arc4.Address,
        amount: arc4.UInt64,
        expiry_days: arc4.UInt64,
        arbiter: arc4.Address,
    ) -> None:
        assert GlobalState.min_balance >= arc4.UInt64(100000), "Insufficient min balance"
        self.client.value = arc4.abi_into(Bytes, arc4.Address(GlobalState.caller))
        self.provider.value = arc4.abi_into(Bytes, provider)
        self.amount.value = amount.native
        self.expiry.value = GlobalState.latest_timestamp + expiry_days * arc4.UInt64(86400)
        self.arbiter.value = arc4.abi_into(Bytes, arbiter)
        self.status.value = String("active")

    @arc4.abimethod()
    def end(self) -> None:
        assert self.status.value == String("active"), "Escrow not active"
        assert GlobalState.caller == arc4.abi_into(arc4.Address, self.provider.value).native, "Only provider can end"
        assert GlobalState.latest_timestamp < self.expiry.value, "Escrow expired"
        self.status.value = String("ended")

    @arc4.abimethod()
    def refund(self) -> None:
        assert self.status.value == String("active"), "Escrow not active"
        assert GlobalState.caller == arc4.abi_into(arc4.Address, self.client.value).native, "Only client can refund"
        assert GlobalState.latest_timestamp >= self.expiry.value, "Escrow not expired"
        self.status.value = String("refunded")

    @arc4.abimethod()
    def arbiter_decide(self, to_provider: arc4.Bool) -> None:
        assert self.status.value == String("active"), "Escrow not active"
        assert GlobalState.caller == arc4.abi_into(arc4.Address, self.arbiter.value).native, "Only arbiter can decide"
        self.status.value = String("ended") if to_provider else String("refunded")