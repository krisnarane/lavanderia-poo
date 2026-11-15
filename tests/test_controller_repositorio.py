from datetime import date

import pytest

from app.controllers.pedido_controller import PedidoController
from app.data.repositorio import Repositorio, RepositorioJson
from app.models.excecoes import ConflitoError, DadoInvalidoError, NaoEncontradoError
from app.models.pedido import Pedido
from app.routes.erros import codigo_para


@pytest.fixture
def arquivo(tmp_path):
    return tmp_path / "pedidos.json"


@pytest.fixture
def ctrl(arquivo):
    return PedidoController(RepositorioJson(arquivo, Pedido.de_dict))


def dados_pedido(comanda="A101", **extra):
    return {
        "comanda": comanda,
        "cliente": "Ana Souza",
        "telefone": "(11) 98765-4321",
        "pecas": [{"tipo": "comum", "descricao": "Camisetas", "quantidade": 2}],
        **extra,
    }


# Repositório abstrato
def test_repositorio_abstrato_nao_pode_ser_instanciado():
    with pytest.raises(TypeError):
        Repositorio()


# RN11 — persistência: os dados continuam depois de "reiniciar"
def test_dados_continuam_no_arquivo(arquivo, ctrl):
    criado = ctrl.criar(dados_pedido())
    reiniciado = PedidoController(RepositorioJson(arquivo, Pedido.de_dict))
    assert reiniciado.buscar(criado["id"]) == criado


def test_status_alterado_fica_salvo(arquivo, ctrl):
    criado = ctrl.criar(dados_pedido())
    ctrl.alterar_status(criado["id"], "lavando")
    reiniciado = PedidoController(RepositorioJson(arquivo, Pedido.de_dict))
    assert reiniciado.buscar(criado["id"])["status"] == "lavando"


# RN12 — comanda não se repete (409)
def test_comanda_duplicada(ctrl):
    ctrl.criar(dados_pedido("A101"))
    with pytest.raises(ConflitoError):
        ctrl.criar(dados_pedido("a101"))


def test_pedido_inexistente(ctrl):
    with pytest.raises(NaoEncontradoError):
        ctrl.buscar(999)


def test_filtro_por_tipo_e_status(ctrl):
    ctrl.criar(dados_pedido("A1"))
    edredom = {"tipo": "edredom", "descricao": "Edredom", "tamanho": "king"}
    ctrl.criar(dados_pedido("A2", pecas=[edredom]))
    assert [p["comanda"] for p in ctrl.listar(tipo="edredom")] == ["A2"]
    assert len(ctrl.listar(status="recebido")) == 2
    assert ctrl.listar(status="pronto") == []


def test_nao_remove_pedido_em_andamento(ctrl):
    criado = ctrl.criar(dados_pedido())
    ctrl.alterar_status(criado["id"], "lavando")
    with pytest.raises(ConflitoError):
        ctrl.remover(criado["id"])


def test_remove_pedido_recebido(ctrl):
    criado = ctrl.criar(dados_pedido())
    ctrl.remover(criado["id"])
    with pytest.raises(NaoEncontradoError):
        ctrl.buscar(criado["id"])


def test_previsao_de_entrega(ctrl):
    criado = ctrl.criar(dados_pedido(data_entrada=date(2026, 11, 9)))
    previsao = ctrl.previsao_entrega(criado["id"])
    assert previsao["prazo_dias"] == 2
    assert previsao["data_prevista"] == "2026-11-11"


# Cada exceção vira o código HTTP certo
@pytest.mark.parametrize(
    "erro, codigo",
    [(NaoEncontradoError("x"), 404), (ConflitoError("x"), 409), (DadoInvalidoError("x"), 422)],
)
def test_traducao_para_http(erro, codigo):
    assert codigo_para(erro) == codigo
