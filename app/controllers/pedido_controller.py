"""Regras de aplicação: buscam no repositório, chamam os models e salvam.

Aqui não existe if sobre o tipo da peça: o cálculo é sempre peca.preco() e
peca.prazo_dias(), e cada classe responde do seu jeito.
"""
from app.data.repositorio import Repositorio
from app.models.excecoes import ConflitoError, NaoEncontradoError
from app.models.peca import TIPOS_PECA, criar_peca
from app.models.pedido import Pedido, StatusPedido


class PedidoController:
    def __init__(self, repositorio: Repositorio):
        self._repo = repositorio

    # ---------- pedidos ----------
    def listar(self, status: str | None = None, tipo: str | None = None) -> list[dict]:
        pedidos = self._repo.listar()
        if status:
            alvo = StatusPedido(status)
            pedidos = [p for p in pedidos if p.status == alvo]
        if tipo:
            pedidos = [p for p in pedidos if p.contem_tipo(tipo)]
        return [p.to_dict() for p in pedidos]

    def _obter(self, pedido_id: int) -> Pedido:
        pedido = self._repo.buscar(pedido_id)
        if pedido is None:
            raise NaoEncontradoError(f"Pedido {pedido_id} não encontrado.")
        return pedido

    def buscar(self, pedido_id: int) -> dict:
        return self._obter(pedido_id).to_dict()

    def criar(self, dados: dict) -> dict:
        pecas = [criar_peca(p) for p in dados.pop("pecas", [])]
        pedido = Pedido(**dados)
        if any(p.comanda == pedido.comanda for p in self._repo.listar()):
            raise ConflitoError(f"Já existe um pedido com a comanda {pedido.comanda}.")
        for peca in pecas:
            pedido.adicionar_peca(peca)
        return self._repo.salvar(pedido).to_dict()

    def atualizar(self, pedido_id: int, dados: dict) -> dict:
        pedido = self._obter(pedido_id)
        if dados.get("cliente") is not None:
            pedido.cliente = dados["cliente"]
        if dados.get("telefone") is not None:
            pedido.telefone = dados["telefone"]
        return self._repo.salvar(pedido).to_dict()

    def remover(self, pedido_id: int) -> None:
        pedido = self._obter(pedido_id)
        pedido.validar_remocao()
        self._repo.remover(pedido_id)

    # ---------- peças do pedido ----------
    def adicionar_peca(self, pedido_id: int, dados: dict) -> dict:
        pedido = self._obter(pedido_id)
        peca = pedido.adicionar_peca(criar_peca(dados))
        self._repo.salvar(pedido)
        return peca.to_dict()

    def remover_peca(self, pedido_id: int, peca_id: int) -> None:
        pedido = self._obter(pedido_id)
        pedido.remover_peca(peca_id)
        self._repo.salvar(pedido)

    # ---------- status ----------
    def alterar_status(self, pedido_id: int, novo_status: str) -> dict:
        pedido = self._obter(pedido_id)
        pedido.alterar_status(novo_status)
        return self._repo.salvar(pedido).to_dict()

    # ---------- cálculo do tema ----------
    def previsao_entrega(self, pedido_id: int) -> dict:
        pedido = self._obter(pedido_id)
        return {
            "pedido_id": pedido.id,
            "comanda": pedido.comanda,
            "data_entrada": pedido.data_entrada.isoformat(),
            "prazo_dias": pedido.prazo_dias(),
            "data_prevista": pedido.data_prevista_entrega().isoformat(),
            "valor_total": pedido.valor_total(),
            "itens": [
                {
                    "peca_id": p.id,
                    "tipo": p.tipo,
                    "descricao": p.descricao,
                    "preco": p.preco(),
                    "prazo_dias": p.prazo_dias(),
                }
                for p in pedido.pecas
            ],
        }

    @staticmethod
    def tabela_precos() -> list[dict]:
        return [classe.tabela() for classe in TIPOS_PECA.values()]
