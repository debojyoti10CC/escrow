from fastapi import FastAPI, Response, HTTPException


app = FastAPI(title="Escrow TEAL API", version="1.0.0")


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "message": "Use /approval or /clear to get TEAL"}


@app.get("/approval")
def get_approval_teal(version: int = 8) -> Response:
    try:
        from pyteal import compileTeal, Mode
        from smart_contracts.mindpal.payment_escrow import approval_program

        teal = compileTeal(approval_program(), mode=Mode.Application, version=version)
        return Response(content=teal, media_type="text/plain")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to compile approval TEAL: {exc}")


@app.get("/clear")
def get_clear_teal(version: int = 8) -> Response:
    try:
        from pyteal import compileTeal, Mode
        from smart_contracts.mindpal.payment_escrow import clear_state_program

        teal = compileTeal(clear_state_program(), mode=Mode.Application, version=version)
        return Response(content=teal, media_type="text/plain")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to compile clear TEAL: {exc}")

