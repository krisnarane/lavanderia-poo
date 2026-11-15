from datetime import date

import pytest

from app.models.excecoes import ConflitoError, DadoInvalidoError, NaoEncontradoError
from app.models.peca import Delicada, Edredom, PecaComum
from app.models.pedido import Pedido, StatusPedido

SEGUNDA = date(2026, 11, 9)
SEXTA = date(2026, 11, 13)


def novo_pedido(data=SEGUNDA, com_pecas=True) -> Pedido:
    pedido = Pedido("A1", "Ana Souza", "11987654321", data_entrada=data)
    if com_pecas:
        pedido.adicionar_peca(PecaComum("Camisetas", 3))
        pedido.adicionar_peca(Edredom("Edredom", "casal"))
    return pedido


def avancar_ate(pedido: Pedido, alvo: StatusPedido) -> None:
    while pedido.status != alvo:
        pedido.alterar_status(pedido.status.proximo())


# RN05 — composição: o pedido calcula a partir das peças que guarda
def test_valor_total_soma_as_pecas():
    assert novo_pedido().valor_total() == 21.00 + 40.00


def test_prazo_do_pedido_e_o_da_peca_mais_demorada():
    pedido = novo_pedido()
    assert pedido.prazo_dias() == 4
    pedido.adicionar_peca(Delicada("Vestido", "seda"))
    assert pedido.prazo_dias() == 5


def test_pedido_sem_pecas_nao_tem_prazo():
    with pytest.raises(DadoInvalidoError):
        novo_pedido(com_pecas=False).prazo_dias()


# RN06 — data prevista de entrega (rota de cálculo)
def test_data_prevista_de_entrega():
    assert novo_pedido(SEGUNDA).data_prevista_entrega() == date(2026, 11, 13)


def test_entrega_que_cairia_no_domingo_passa_para_segunda():
    pedido = Pedido("A2", "Ana Souza", "11987654321", data_entrada=SEXTA)
    pedido.adicionar_peca(PecaComum("Calça", 1))  # sexta + 2 dias = domingo
    assert pedido.data_prevista_entrega() == date(2026, 11, 16)


# RN07 — status só avança na ordem
def test_status_avanca_na_ordem():
    pedido = novo_pedido()
    for esperado in ["lavando", "pronto", "entregue"]:
        pedido.alterar_status(esperado)
        assert pedido.status.value == esperado


def test_status_nao_pula_etapa():
    pedido = novo_pedido()
    with pytest.raises(ConflitoError):
        pedido.alterar_status("pronto")


def test_status_nao_volta():
    pedido = novo_pedido()
    avancar_ate(pedido, StatusPedido.PRONTO)
    with pytest.raises(ConflitoError):
        pedido.alterar_status("lavando")


def test_status_inexistente():
    with pytest.raises(DadoInvalidoError):
        novo_pedido().alterar_status("passando")


def test_nao_comeca_a_lavar_sem_pecas():
    with pytest.raises(ConflitoError):
        novo_pedido(com_pecas=False).alterar_status("lavando")


# RN08 — pedido só é entregue depois de pronto
def test_nao_entrega_pedido_que_ainda_esta_lavando():
    pedido = novo_pedido()
    pedido.alterar_status("lavando")
    with pytest.raises(ConflitoError):
        pedido.alterar_status("entregue")


def test_entrega_depois_de_pronto_registra_a_data():
    pedido = novo_pedido()
    avancar_ate(pedido, StatusPedido.PRONTO)
    pedido.alterar_status("entregue")
    assert pedido.data_entrega == date.today()


def test_pedido_entregue_nao_muda_mais():
    pedido = novo_pedido()
    avancar_ate(pedido, StatusPedido.ENTREGUE)
    with pytest.raises(ConflitoError):
        pedido.alterar_status("entregue")


# RN09 — peças só mudam enquanto o pedido está "recebido"
def test_nao_adiciona_peca_depois_de_comecar_a_lavar():
    pedido = novo_pedido()
    pedido.alterar_status("lavando")
    with pytest.raises(ConflitoError):
        pedido.adicionar_peca(PecaComum("Meias", 2))


def test_remover_peca_inexistente():
    with pytest.raises(NaoEncontradoError):
        novo_pedido().remover_peca(99)


def test_ids_das_pecas_sao_sequenciais():
    assert [p.id for p in novo_pedido().pecas] == [1, 2]


# RN10 — dados do pedido validados no model
def test_telefone_invalido():
    with pytest.raises(DadoInvalidoError):
        Pedido("A1", "Ana Souza", "1234")


def test_comanda_invalida():
    with pytest.raises(DadoInvalidoError):
        Pedido("A-1!", "Ana Souza", "11987654321")


def test_data_de_entrada_no_futuro():
    with pytest.raises(DadoInvalidoError):
        Pedido("A1", "Ana Souza", "11987654321", data_entrada=date(2999, 1, 1))


def test_status_nao_tem_setter():
    with pytest.raises(AttributeError):
        novo_pedido().status = StatusPedido.ENTREGUE


def test_ida_e_volta_pelo_dicionario():
    original = novo_pedido()
    original.id = 7
    copia = Pedido.de_dict(original.to_dict())
    assert copia.to_dict() == original.to_dict()
