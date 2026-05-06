from fastapi import FastAPI

app = FastAPI(title="Nomina Service")


@app.get("/health")
def health():
    return {"status": "ok", "service": "nomina"}


@app.get("/payroll")
def payroll():
    # Minimal placeholder endpoint
    return {"message": "Servicio de nómina mínimo funcionando"}
