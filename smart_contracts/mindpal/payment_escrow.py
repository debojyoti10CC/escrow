from pyteal import *


def approval_program():
    session_amount = Bytes("session_amount")
    session_start = Bytes("session_start")
    vpn_provider = Bytes("vpn_provider")
    user = Bytes("user")

    CREATE_SESSION = Bytes("create_session")
    END_SESSION = Bytes("end_session")

    @Subroutine(TealType.uint64)
    def is_provider() -> Expr:
        return Eq(Txn.sender(), App.globalGet(vpn_provider))

    @Subroutine(TealType.uint64)
    def is_user() -> Expr:
        return Eq(Txn.sender(), App.globalGet(user))

    on_creation = Seq(
        App.globalPut(session_amount, Int(0)),
        App.globalPut(session_start, Int(0)),
        App.globalPut(vpn_provider, Bytes("")),
        App.globalPut(user, Bytes("")),
        Approve(),
    )

    on_create_session = Seq(
        Assert(Txn.application_args.length() == Int(3)),
        Assert(Global.group_size() >= Int(2)),
        Assert(Gtxn[1].type_enum() == TxnType.Payment),
        Assert(Gtxn[1].receiver() == Global.current_application_address()),
        Assert(Gtxn[1].amount() == Btoi(Txn.application_args[2])),
        App.globalPut(vpn_provider, Txn.application_args[1]),
        App.globalPut(user, Txn.sender()),
        App.globalPut(session_amount, Btoi(Txn.application_args[2])),
        App.globalPut(session_start, Global.latest_timestamp()),
        Approve(),
    )

    on_end_session = Seq(
        Assert(Or(is_provider(), is_user())),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: App.globalGet(vpn_provider),
                TxnField.amount: App.globalGet(session_amount),
                TxnField.fee: Global.min_txn_fee(),
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve(),
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.NoOp, Cond(
            [Txn.application_args[0] == CREATE_SESSION, on_create_session],
            [Txn.application_args[0] == END_SESSION, on_end_session],
        )],
    )

    return program


def clear_state_program():
    return Approve()


if __name__ == "__main__":
    print(compileTeal(approval_program(), mode=Mode.Application, version=8))
    print("\n==== CLEAR STATE ====\n")
    print(compileTeal(clear_state_program(), mode=Mode.Application, version=8))

