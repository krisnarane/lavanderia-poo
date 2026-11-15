"""Pedido: guarda as peças (composição) e controla o status."""
from datetime import date, timedelta
from enum import Enum

from app.models.excecoes import ConflitoError, DadoInvalidoError, NaoEncontradoError
from app.models.peca import Peca, criar_peca


class StatusPedido(str, Enum):
    """Status na ordem em que acontecem. A ordem da declaração é a regra."""

    RECEBIDO = "recebido"
    LAVANDO = "lavando"
    PRONTO = "pronto"
    ENTREGUE = "entregue"

    def proximo(self) -> "StatusPedido | None":
        ordem = list(StatusPedido)
        posicao = ordem.index(self)
        return ordem[posicao + 1] if posicao + 1 < len(ordem) else None


class Pedido:
    DIA_SEM_ENTREGA = 6  # domingo (date.weekday(): segunda=0 ... domingo=6)
    MAX_PECAS = 30

    def __init__(
        self,
        comanda: str,
        cliente: str,
        telefone: str,
        pecas: list[Peca] | None = None,
        data_entrada: date | None = None,
        status: StatusPedido = StatusPedido.RECEBIDO,
        data_entrega: date | None = None,
        id: int | None = None,
    ):
        self._id = id
        self.comanda = comanda
        self.cliente = cliente
        self.telefone = telefone
        self.data_entrada = data_entrada or date.today()
        self._status = StatusPedido(status)
        self._data_entrega = data_entrega
        self._pecas: list[Peca] = list(pecas or [])

    # ---------- encapsulamento ----------
    @property
    def id(self) -> int | None:
        return self._id

    @id.setter
    def id(self, valor: int) -> None:
        if self._id is not None:
            raise DadoInvalidoError("O id do pedido já foi definido e não pode mudar.")
        self._id = valor

    @property
    def comanda(self) -> str:
        return self._comanda

    @comanda.setter
    def comanda(self, valor: str) -> None:
        valor = (valor or "").strip().upper()
        if not (2 <= len(valor) <= 10) or not valor.isalnum():
            raise DadoInvalidoError("A comanda precisa ter de 2 a 10 letras ou números.")
        self._comanda = valor

    @property
    def cliente(self) -> str:
        return self._cliente

    @cliente.setter
    def cliente(self, valor: str) -> None:
        valor = (valor or "").strip()
        if len(valor) < 3:
            raise DadoInvalidoError("O nome do cliente precisa ter pelo menos 3 letras.")
        self._cliente = valor

    @property
    def telefone(self) -> str:
        return self._telefone

    @telefone.setter
    def telefone(self, valor: str) -> None:
        digitos = "".join(c for c in (valor or "") if c.isdigit())
        if len(digitos) not in (10, 11):
            raise DadoInvalidoError("O telefone precisa ter DDD + número (10 ou 11 dígitos).")
        self._telefone = digitos

    @property
    def data_entrada(self) -> date:
        return self._data_entrada

    @data_entrada.setter
    def data_entrada(self, valor: date) -> None:
        if valor > date.today():
            raise DadoInvalidoError("A data de entrada não pode estar no futuro.")
        self._data_entrada = valor

    @property
    def status(self) -> StatusPedido:
        return self._status  # sem setter: só muda por alterar_status()

    @property
    def data_entrega(self) -> date | None:
        return self._data_entrega

    @property
    def pecas(self) -> list[Peca]:
        return list(self._pecas)  # cópia: ninguém mexe na lista por fora

    # ---------- peças (composição) ----------
    def _exigir_recebido(self, acao: str) -> None:
        if self._status != StatusPedido.RECEBIDO:
            raise ConflitoError(
                f"Não é possível {acao}: o pedido já está '{self._status.value}'."
            )

    def adicionar_peca(self, peca: Peca) -> Peca:
        self._exigir_recebido("adicionar peças")
        if len(self._pecas) >= self.MAX_PECAS:
            raise ConflitoError(f"O pedido já tem o máximo de {self.MAX_PECAS} itens.")
        peca.id = max((p.id for p in self._pecas), default=0) + 1
        self._pecas.append(peca)
        return peca

    def remover_peca(self, peca_id: int) -> None:
        self._exigir_recebido("remover peças")
        peca = self.buscar_peca(peca_id)
        self._pecas.remove(peca)

    def buscar_peca(self, peca_id: int) -> Peca:
        for peca in self._pecas:
            if peca.id == peca_id:
                return peca
        raise NaoEncontradoError(f"Peça {peca_id} não encontrada no pedido {self._id}.")

    def contem_tipo(self, tipo: str) -> bool:
        return tipo in {p.tipo for p in self._pecas}

    # ---------- cálculos (usam as peças guardadas) ----------
    def valor_total(self) -> float:
        return round(sum(p.preco() for p in self._pecas), 2)

    def prazo_dias(self) -> int:
        """O pedido fica pronto quando a peça mais demorada fica pronta."""
        if not self._pecas:
            raise DadoInvalidoError("O pedido não tem peças, então não tem prazo.")
        return max(p.prazo_dias() for p in self._pecas)

    def data_prevista_entrega(self) -> date:
        prevista = self._data_entrada + timedelta(days=self.prazo_dias())
        if prevista.weekday() == self.DIA_SEM_ENTREGA:
            prevista += timedelta(days=1)
        return prevista

    # ---------- status ----------
    def alterar_status(self, novo: str | StatusPedido) -> None:
        try:
            novo = StatusPedido(novo)
        except ValueError:
            opcoes = ", ".join(s.value for s in StatusPedido)
            raise DadoInvalidoError(f"Status inválido. Use: {opcoes}.")

        esperado = self._status.proximo()
        if esperado is None:
            raise ConflitoError("O pedido já foi entregue; o status não muda mais.")
        if novo == StatusPedido.ENTREGUE and self._status != StatusPedido.PRONTO:
            raise ConflitoError("O pedido só pode ser entregue depois de estar pronto.")
        if novo != esperado:
            raise ConflitoError(
                f"O status só avança na ordem: de '{self._status.value}' "
                f"o próximo é '{esperado.value}'."
            )
        if novo == StatusPedido.LAVANDO and not self._pecas:
            raise ConflitoError("Não dá para começar a lavar um pedido sem peças.")

        self._status = novo
        if novo == StatusPedido.ENTREGUE:
            self._data_entrega = date.today()

    def validar_remocao(self) -> None:
        self._exigir_recebido("remover o pedido")

    # ---------- conversão para JSON ----------
    def to_dict(self) -> dict:
        return {
            "id": self._id,
            "comanda": self._comanda,
            "cliente": self._cliente,
            "telefone": self._telefone,
            "data_entrada": self._data_entrada.isoformat(),
            "status": self._status.value,
            "data_entrega": self._data_entrega.isoformat() if self._data_entrega else None,
            "pecas": [p.to_dict() for p in self._pecas],
            "valor_total": self.valor_total(),
        }

    @classmethod
    def de_dict(cls, dados: dict) -> "Pedido":
        entrega = dados.get("data_entrega")
        return cls(
            id=dados.get("id"),
            comanda=dados["comanda"],
            cliente=dados["cliente"],
            telefone=dados["telefone"],
            data_entrada=date.fromisoformat(dados["data_entrada"]),
            status=StatusPedido(dados.get("status", "recebido")),
            data_entrega=date.fromisoformat(entrega) if entrega else None,
            pecas=[criar_peca(p) for p in dados.get("pecas", [])],
        )
