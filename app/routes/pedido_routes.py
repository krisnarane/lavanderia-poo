"""Rotas: recebem a requisição, chamam o controller e devolvem a resposta.

Nenhuma regra de negócio aqui.
"""
from fastapi import APIRouter, Depends, Response, status

from app.controllers.pedido_controller import PedidoController
from app.data.repositorio import PASTA_DADOS, RepositorioJson
from app.models.pedido import Pedido, StatusPedido
from app.routes.schemas import PecaEntrada, PedidoAlteracao, PedidoEntrada, StatusEntrada, TipoPeca

router = APIRouter(tags=["Lavanderia"])

_controller = PedidoController(RepositorioJson(PASTA_DADOS / "pedidos.json", Pedido.de_dict))


def get_controller() -> PedidoController:
    return _controller


@router.get("/pecas/tabela-precos", summary="Tabela de preços e prazos por tipo de peça")
def tabela_precos(ctrl: PedidoController = Depends(get_controller)):
    return ctrl.tabela_precos()


@router.get("/pedidos", summary="Listar pedidos (filtros opcionais ?status= e ?tipo=)")
def listar_pedidos(
    status: StatusPedido | None = None,
    tipo: TipoPeca | None = None,
    ctrl: PedidoController = Depends(get_controller),
):
    return ctrl.listar(status=status.value if status else None, tipo=tipo)


@router.get("/pedidos/{pedido_id}", summary="Buscar pedido por id")
def buscar_pedido(pedido_id: int, ctrl: PedidoController = Depends(get_controller)):
    return ctrl.buscar(pedido_id)


@router.post("/pedidos", status_code=status.HTTP_201_CREATED, summary="Criar pedido")
def criar_pedido(entrada: PedidoEntrada, ctrl: PedidoController = Depends(get_controller)):
    dados = entrada.model_dump(exclude_none=True)
    return ctrl.criar(dados)


@router.patch("/pedidos/{pedido_id}", summary="Alterar nome ou telefone do cliente")
def alterar_pedido(
    pedido_id: int, entrada: PedidoAlteracao, ctrl: PedidoController = Depends(get_controller)
):
    return ctrl.atualizar(pedido_id, entrada.model_dump(exclude_none=True))


@router.delete(
    "/pedidos/{pedido_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover pedido"
)
def remover_pedido(pedido_id: int, ctrl: PedidoController = Depends(get_controller)):
    ctrl.remover(pedido_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/pedidos/{pedido_id}/pecas",
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar peça ao pedido",
)
def adicionar_peca(
    pedido_id: int, entrada: PecaEntrada, ctrl: PedidoController = Depends(get_controller)
):
    return ctrl.adicionar_peca(pedido_id, entrada.model_dump(exclude_none=True))


@router.delete(
    "/pedidos/{pedido_id}/pecas/{peca_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover peça do pedido",
)
def remover_peca(pedido_id: int, peca_id: int, ctrl: PedidoController = Depends(get_controller)):
    ctrl.remover_peca(pedido_id, peca_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/pedidos/{pedido_id}/status", summary="Avançar o status do pedido")
def alterar_status(
    pedido_id: int, entrada: StatusEntrada, ctrl: PedidoController = Depends(get_controller)
):
    return ctrl.alterar_status(pedido_id, entrada.status)


@router.get("/pedidos/{pedido_id}/entrega", summary="Cálculo: data prevista de entrega")
def previsao_entrega(pedido_id: int, ctrl: PedidoController = Depends(get_controller)):
    return ctrl.previsao_entrega(pedido_id)
