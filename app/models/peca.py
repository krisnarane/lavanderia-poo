"""Hierarquia das peças: Peca (abstrata) -> PecaComum, Edredom, Delicada.

Cada filha responde do seu jeito a preco() e prazo_dias(). Quem usa uma peça
não precisa saber qual é o tipo dela: basta chamar os métodos (polimorfismo).
"""
from abc import ABC, abstractmethod

from app.models.excecoes import DadoInvalidoError


class Peca(ABC):
    TIPO = ""
    MAX_QUANTIDADE = 50

    def __init__(self, descricao: str, quantidade: int = 1, id: int | None = None):
        self._id = id
        self.descricao = descricao
        self.quantidade = quantidade

    # ---------- encapsulamento ----------
    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        if self._id is not None:
            raise DadoInvalidoError("O id da peça já foi definido e não pode mudar.")
        self._id = valor

    @property
    def descricao(self) -> str:
        return self._descricao

    @descricao.setter
    def descricao(self, valor: str) -> None:
        valor = (valor or "").strip()
        if len(valor) < 3:
            raise DadoInvalidoError("A descrição da peça precisa ter pelo menos 3 letras.")
        self._descricao = valor

    @property
    def quantidade(self) -> int:
        return self._quantidade

    @quantidade.setter
    def quantidade(self, valor: int) -> None:
        if not isinstance(valor, int) or valor < 1:
            raise DadoInvalidoError("A quantidade precisa ser um número inteiro maior que zero.")
        if valor > self.MAX_QUANTIDADE:
            raise DadoInvalidoError(
                f"No máximo {self.MAX_QUANTIDADE} unidades de '{self.TIPO}' por item."
            )
        self._quantidade = valor

    @property
    def tipo(self) -> str:
        return self.TIPO

    # ---------- regras polimórficas ----------
    @abstractmethod
    def preco(self) -> float:
        """Valor cobrado por este item (já multiplicado pela quantidade)."""

    @abstractmethod
    def prazo_dias(self) -> int:
        """Quantos dias este tipo de peça leva para ficar pronto."""

    @classmethod
    @abstractmethod
    def tabela(cls) -> dict:
        """Preço e prazo deste tipo, para a tabela de preços."""

    # ---------- conversão para JSON ----------
    def _extras(self) -> dict:
        """Atributos próprios da filha. Por padrão, nenhum."""
        return {}

    @classmethod
    def _extras_de(cls, dados: dict) -> dict:
        """Lê do dicionário os atributos próprios da filha."""
        return {}

    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "tipo": self.tipo,
            "descricao": self._descricao,
            "quantidade": self._quantidade,
            **self._extras(),
            "preco": self.preco(),
            "prazo_dias": self.prazo_dias(),
        }

    @classmethod
    def de_dict(cls, dados: dict) -> "Peca":
        return cls(
            descricao=dados.get("descricao"),
            quantidade=dados.get("quantidade", 1),
            id=dados.get("id"),
            **cls._extras_de(dados),
        )


class PecaComum(Peca):
    """Roupa do dia a dia: camiseta, calça, toalha. Lavagem em máquina."""

    TIPO = "comum"
    PRECO_UNITARIO = 7.00
    PRAZO_DIAS = 2

    def __init__(self, descricao: str, quantidade: int = 1, id: int | None = None):
        super().__init__(descricao, quantidade, id)

    def preco(self) -> float:
        return round(self.PRECO_UNITARIO * self.quantidade, 2)

    def prazo_dias(self) -> int:
        return self.PRAZO_DIAS

    @classmethod
    def tabela(cls) -> dict:
        return {
            "tipo": cls.TIPO,
            "preco": f"R$ {cls.PRECO_UNITARIO:.2f} por unidade",
            "prazo_dias": cls.PRAZO_DIAS,
        }


class Edredom(Peca):
    """Peça grande: o preço depende do tamanho e a secagem demora mais."""

    TIPO = "edredom"
    PRECO_POR_TAMANHO = {"solteiro": 30.00, "casal": 40.00, "king": 50.00}
    PRAZO_DIAS = 4
    MAX_QUANTIDADE = 5

    def __init__(self, descricao: str, tamanho: str, quantidade: int = 1, id: int | None = None):
        super().__init__(descricao, quantidade, id)
        self.tamanho = tamanho

    @property
    def tamanho(self) -> str:
        return self._tamanho

    @tamanho.setter
    def tamanho(self, valor: str) -> None:
        valor = (valor or "").strip().lower()
        if valor not in self.PRECO_POR_TAMANHO:
            opcoes = ", ".join(self.PRECO_POR_TAMANHO)
            raise DadoInvalidoError(f"Tamanho de edredom inválido. Use: {opcoes}.")
        self._tamanho = valor

    def preco(self) -> float:
        return round(self.PRECO_POR_TAMANHO[self.tamanho] * self.quantidade, 2)

    def prazo_dias(self) -> int:
        return self.PRAZO_DIAS

    @classmethod
    def tabela(cls) -> dict:
        precos = ", ".join(f"{t} R$ {v:.2f}" for t, v in cls.PRECO_POR_TAMANHO.items())
        return {"tipo": cls.TIPO, "preco": f"por unidade: {precos}", "prazo_dias": cls.PRAZO_DIAS}

    def _extras(self) -> dict:
        return {"tamanho": self.tamanho}

    @classmethod
    def _extras_de(cls, dados: dict) -> dict:
        return {"tamanho": dados.get("tamanho")}


class Delicada(Peca):
    """Lavagem à mão e secagem natural: preço base mais acréscimo pelo tecido."""

    TIPO = "delicada"
    PRECO_BASE = 15.00
    ACRESCIMO_POR_TECIDO = {"seda": 10.00, "renda": 8.00, "la": 6.00, "linho": 4.00}
    PRAZO_DIAS = 5
    MAX_QUANTIDADE = 10

    def __init__(self, descricao: str, tecido: str, quantidade: int = 1, id: int | None = None):
        super().__init__(descricao, quantidade, id)
        self.tecido = tecido

    @property
    def tecido(self) -> str:
        return self._tecido

    @tecido.setter
    def tecido(self, valor: str) -> None:
        valor = (valor or "").strip().lower()
        if valor not in self.ACRESCIMO_POR_TECIDO:
            opcoes = ", ".join(self.ACRESCIMO_POR_TECIDO)
            raise DadoInvalidoError(f"Tecido inválido para peça delicada. Use: {opcoes}.")
        self._tecido = valor

    def preco(self) -> float:
        unitario = self.PRECO_BASE + self.ACRESCIMO_POR_TECIDO[self.tecido]
        return round(unitario * self.quantidade, 2)

    def prazo_dias(self) -> int:
        return self.PRAZO_DIAS

    @classmethod
    def tabela(cls) -> dict:
        acres = ", ".join(f"{t} +R$ {v:.2f}" for t, v in cls.ACRESCIMO_POR_TECIDO.items())
        return {
            "tipo": cls.TIPO,
            "preco": f"R$ {cls.PRECO_BASE:.2f} por unidade + tecido ({acres})",
            "prazo_dias": cls.PRAZO_DIAS,
        }

    def _extras(self) -> dict:
        return {"tecido": self.tecido}

    @classmethod
    def _extras_de(cls, dados: dict) -> dict:
        return {"tecido": dados.get("tecido")}


# Dicionário de tipos: troca um if/elif por uma consulta. Para criar um tipo
# novo, basta escrever a classe e acrescentar uma linha aqui.
TIPOS_PECA: dict[str, type[Peca]] = {
    PecaComum.TIPO: PecaComum,
    Edredom.TIPO: Edredom,
    Delicada.TIPO: Delicada,
}


def criar_peca(dados: dict) -> Peca:
    classe = TIPOS_PECA.get(dados.get("tipo"))
    if classe is None:
        raise DadoInvalidoError(f"Tipo de peça inválido. Use: {', '.join(TIPOS_PECA)}.")
    return classe.de_dict(dados)
