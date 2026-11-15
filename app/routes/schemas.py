"""Schemas do Pydantic: conferem só o FORMATO da entrada.

As regras (tamanho válido, tecido válido, telefone, ordem do status...) ficam
nos models.
"""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

TipoPeca = Literal["comum", "edredom", "delicada"]


class PecaEntrada(BaseModel):
    tipo: TipoPeca
    descricao: str = Field(min_length=1, max_length=80)
    quantidade: int = Field(default=1, ge=1)
    tamanho: str | None = Field(default=None, description="Só para edredom: solteiro, casal, king")
    tecido: str | None = Field(default=None, description="Só para delicada: seda, renda, la, linho")

    model_config = {
        "json_schema_extra": {
            "example": {"tipo": "edredom", "descricao": "Edredom florido", "quantidade": 1, "tamanho": "casal"}
        }
    }


class PedidoEntrada(BaseModel):
    comanda: str = Field(min_length=1, max_length=20)
    cliente: str = Field(min_length=1, max_length=100)
    telefone: str = Field(min_length=1, max_length=20)
    data_entrada: date | None = None
    pecas: list[PecaEntrada] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "comanda": "A101",
                "cliente": "Ana Souza",
                "telefone": "(11) 98765-4321",
                "pecas": [
                    {"tipo": "comum", "descricao": "Camisetas", "quantidade": 4},
                    {"tipo": "delicada", "descricao": "Vestido de festa", "quantidade": 1, "tecido": "seda"},
                ],
            }
        }
    }


class PedidoAlteracao(BaseModel):
    cliente: str | None = Field(default=None, min_length=1, max_length=100)
    telefone: str | None = Field(default=None, min_length=1, max_length=20)


class StatusEntrada(BaseModel):
    status: str = Field(description="recebido, lavando, pronto ou entregue", examples=["lavando"])
