"""Exceções de negócio da lavanderia.

Os models só levantam estas exceções. Quem decide o código HTTP de cada uma
é a camada de rotas (app/routes/erros.py).
"""


class ErroNegocio(Exception):
    """Base de todo erro de regra de negócio do sistema."""

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class NaoEncontradoError(ErroNegocio):
    """O registro procurado não existe (vira 404)."""


class ConflitoError(ErroNegocio):
    """A operação conflita com o estado atual dos dados (vira 409)."""


class DadoInvalidoError(ErroNegocio):
    """O dado chegou no formato certo, mas quebra uma regra (vira 422)."""
