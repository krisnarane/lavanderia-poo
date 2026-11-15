import pytest

from app.models.excecoes import DadoInvalidoError
from app.models.peca import Delicada, Edredom, Peca, PecaComum, criar_peca


# RN01 — Peca é abstrata
def test_peca_abstrata_nao_pode_ser_instanciada():
    with pytest.raises(TypeError):
        Peca("Qualquer coisa", 1)


# RN02 — preco() polimórfico
def test_preco_peca_comum_por_unidade():
    assert PecaComum("Camisetas", 4).preco() == 28.00


def test_preco_edredom_depende_do_tamanho():
    assert Edredom("Edredom", "solteiro").preco() == 30.00
    assert Edredom("Edredom", "king", 2).preco() == 100.00


def test_preco_delicada_soma_acrescimo_do_tecido():
    assert Delicada("Vestido", "seda").preco() == 25.00
    assert Delicada("Blusas", "linho", 3).preco() == 57.00


def test_mesmo_metodo_para_qualquer_filha():
    pecas = [PecaComum("Calça", 1), Edredom("Edredom", "casal"), Delicada("Saia", "renda")]
    assert [p.preco() for p in pecas] == [7.00, 40.00, 23.00]


# RN03 — prazo_dias() polimórfico
def test_prazo_por_tipo():
    assert PecaComum("Calça", 1).prazo_dias() == 2
    assert Edredom("Edredom", "casal").prazo_dias() == 4
    assert Delicada("Saia", "renda").prazo_dias() == 5


# RN04 — validação nos setters
def test_quantidade_precisa_ser_positiva():
    with pytest.raises(DadoInvalidoError):
        PecaComum("Camiseta", 0)


def test_quantidade_maxima_por_tipo():
    with pytest.raises(DadoInvalidoError):
        Edredom("Edredom", "casal", Edredom.MAX_QUANTIDADE + 1)


def test_tamanho_de_edredom_invalido():
    with pytest.raises(DadoInvalidoError):
        Edredom("Edredom", "gigante")


def test_tecido_de_delicada_invalido():
    with pytest.raises(DadoInvalidoError):
        Delicada("Vestido", "jeans")


def test_descricao_curta_e_invalida():
    with pytest.raises(DadoInvalidoError):
        PecaComum("ab", 1)


def test_criar_peca_pelo_tipo():
    peca = criar_peca({"tipo": "delicada", "descricao": "Vestido", "tecido": "seda"})
    assert isinstance(peca, Delicada)


def test_criar_peca_com_tipo_desconhecido():
    with pytest.raises(DadoInvalidoError):
        criar_peca({"tipo": "tapete", "descricao": "Tapete"})
