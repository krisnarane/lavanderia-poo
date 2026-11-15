"""Persistência: Repositorio (abstrato) e RepositorioJson (arquivo .json)."""
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

PASTA_DADOS = Path(__file__).resolve().parent


class Repositorio(ABC):
    """Contrato de qualquer repositório. O controller só conhece esta classe."""

    @abstractmethod
    def listar(self) -> list: ...

    @abstractmethod
    def buscar(self, id: int): ...

    @abstractmethod
    def salvar(self, objeto): ...

    @abstractmethod
    def remover(self, id: int) -> bool: ...


class RepositorioJson(Repositorio):
    """Guarda os objetos em um arquivo JSON.

    O objeto precisa ter id, to_dict(); e quem cria o repositório informa a
    função que transforma o dicionário de volta em objeto (ex.: Pedido.de_dict).
    """

    def __init__(self, caminho: str | Path, de_dict: Callable[[dict], object]):
        self._caminho = Path(caminho)
        self._de_dict = de_dict
        if not self._caminho.exists():
            self._caminho.parent.mkdir(parents=True, exist_ok=True)
            self._gravar({"proximo_id": 1, "itens": []})

    # ---------- arquivo ----------
    def _ler(self) -> dict:
        with open(self._caminho, encoding="utf-8") as arq:
            return json.load(arq)

    def _gravar(self, conteudo: dict) -> None:
        temporario = self._caminho.with_suffix(".tmp")
        with open(temporario, "w", encoding="utf-8") as arq:
            json.dump(conteudo, arq, ensure_ascii=False, indent=2)
        os.replace(temporario, self._caminho)  # troca de uma vez: não corrompe o arquivo

    # ---------- operações ----------
    def listar(self) -> list:
        return [self._de_dict(item) for item in self._ler()["itens"]]

    def buscar(self, id: int):
        for item in self._ler()["itens"]:
            if item["id"] == id:
                return self._de_dict(item)
        return None

    def salvar(self, objeto):
        conteudo = self._ler()
        if objeto.id is None:
            objeto.id = conteudo["proximo_id"]
            conteudo["proximo_id"] += 1
        dados = objeto.to_dict()
        itens = [i for i in conteudo["itens"] if i["id"] != objeto.id]
        itens.append(dados)
        conteudo["itens"] = sorted(itens, key=lambda i: i["id"])
        self._gravar(conteudo)
        return objeto

    def remover(self, id: int) -> bool:
        conteudo = self._ler()
        restantes = [i for i in conteudo["itens"] if i["id"] != id]
        if len(restantes) == len(conteudo["itens"]):
            return False
        conteudo["itens"] = restantes
        self._gravar(conteudo)
        return True
