from fastapi import FastAPI

from app.routes.erros import registrar_tratadores
from app.routes.pedido_routes import router

app = FastAPI(
    title="Lavanderia API",
    description="Prova final de POO — FATEC Mogi das Cruzes. Tema 6: Lavanderia.",
    version="1.0.0",
)

registrar_tratadores(app)
app.include_router(router)


@app.get("/", tags=["Info"])
def inicio():
    return {"sistema": "Lavanderia API", "documentacao": "/docs"}
