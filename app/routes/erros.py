"""Tradução das exceções de negócio para códigos HTTP.

Nenhuma regra de negócio termina em 500: toda ErroNegocio vira uma resposta
com o código certo.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.models.excecoes import ConflitoError, DadoInvalidoError, ErroNegocio, NaoEncontradoError

CODIGO_HTTP: dict[type[ErroNegocio], int] = {
    NaoEncontradoError: 404,
    ConflitoError: 409,
    DadoInvalidoError: 422,
}


def codigo_para(erro: ErroNegocio) -> int:
    for classe in type(erro).__mro__:  # aceita também subclasses das três
        if classe in CODIGO_HTTP:
            return CODIGO_HTTP[classe]
    return 400  # erro de negócio sem código próprio: culpa da requisição


def registrar_tratadores(app: FastAPI) -> None:
    @app.exception_handler(ErroNegocio)
    async def tratar_erro_negocio(request: Request, erro: ErroNegocio):
        return JSONResponse(
            status_code=codigo_para(erro),
            content={"erro": type(erro).__name__, "detalhe": erro.mensagem},
        )
