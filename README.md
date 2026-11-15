# Lavanderia API

Prova final de Programação Orientada a Objetos — FATEC Mogi das Cruzes (ADS).
Tema 6: **Lavanderia**. Backend em Python com FastAPI, em quatro camadas.

O sistema registra os pedidos que chegam ao balcão de uma lavanderia: cada pedido
tem uma comanda, o cliente e as peças. Ele calcula o preço, o prazo e a data
prevista de entrega, e controla o andamento do pedido até a retirada.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger: http://127.0.0.1:8000/docs

Testes (na raiz do projeto):

```bash
pytest
```

## Estrutura

```
app/
  data/          pedidos.json e repositorio.py (Repositorio abstrato + RepositorioJson)
  models/        peca.py, pedido.py, excecoes.py
  controllers/   pedido_controller.py
  routes/        pedido_routes.py, schemas.py (Pydantic), erros.py (exceção -> HTTP)
tests/           pytest
docs/            diagrama_classes.puml (PlantUML)
main.py
requirements.txt
```

## Regras de negócio

| Regra | Descrição | Valores |
|---|---|---|
| RN01 | `Peca` é abstrata; só existem peças dos tipos concretos | comum, edredom, delicada |
| RN02 | `preco()` é calculado por tipo | Comum R$ 7,00/un. · Edredom: solteiro R$ 30, casal R$ 40, king R$ 50 · Delicada R$ 15 + tecido (seda +10, renda +8, lã +6, linho +4) |
| RN03 | `prazo_dias()` é calculado por tipo | Comum 2 dias · Edredom 4 · Delicada 5 |
| RN04 | Quantidade mínima de 1 e máxima por item | Comum 50 · Edredom 5 · Delicada 10 |
| RN05 | O valor do pedido é a soma das peças e o prazo é o da peça mais demorada | — |
| RN06 | Data prevista = data de entrada + prazo; se cair no domingo, passa para segunda | loja fechada no domingo |
| RN07 | O status só avança na ordem, sem pular nem voltar | recebido → lavando → pronto → entregue |
| RN08 | O pedido só é entregue depois de pronto; a data de entrega é registrada | — |
| RN09 | Peças só podem ser incluídas ou removidas, e o pedido só pode ser apagado, enquanto está "recebido"; não se começa a lavar sem peças | máx. 30 itens por pedido |
| RN10 | Validação de dados: comanda de 2 a 10 letras/números, cliente com 3+ letras, telefone com DDD (10 ou 11 dígitos), data de entrada não futura | — |
| RN11 | Os pedidos ficam salvos em `app/data/pedidos.json` | — |
| RN12 | Não existem duas comandas iguais | — |

## Rotas

| Método | Caminho | O que faz | Códigos |
|---|---|---|---|
| GET | `/pecas/tabela-precos` | Preço e prazo de cada tipo de peça | 200 |
| GET | `/pedidos?status=&tipo=` | Lista pedidos; filtra por status e/ou tipo de peça | 200, 422 |
| GET | `/pedidos/{id}` | Busca um pedido | 200, 404 |
| POST | `/pedidos` | Cria um pedido (pode já vir com peças) | 201, 409, 422 |
| PATCH | `/pedidos/{id}` | Altera nome ou telefone do cliente | 200, 404, 422 |
| DELETE | `/pedidos/{id}` | Remove um pedido "recebido" | 204, 404, 409 |
| POST | `/pedidos/{id}/pecas` | Inclui uma peça no pedido | 201, 404, 409, 422 |
| DELETE | `/pedidos/{id}/pecas/{peca_id}` | Remove uma peça do pedido | 204, 404, 409 |
| PATCH | `/pedidos/{id}/status` | Avança o status | 200, 404, 409, 422 |
| GET | `/pedidos/{id}/entrega` | **Cálculo:** data prevista de entrega, prazo e valor | 200, 404, 422 |

Exemplo — `POST /pedidos`:

```json
{
  "comanda": "A101",
  "cliente": "Ana Souza",
  "telefone": "(11) 98765-4321",
  "pecas": [
    {"tipo": "comum", "descricao": "Camisetas", "quantidade": 4},
    {"tipo": "delicada", "descricao": "Vestido de festa", "tecido": "seda"}
  ]
}
```

Exemplo de resposta — `GET /pedidos/1/entrega`:

```json
{
  "pedido_id": 1,
  "comanda": "A101",
  "data_entrada": "2026-11-14",
  "prazo_dias": 5,
  "data_prevista": "2026-11-19",
  "valor_total": 53.0,
  "itens": [
    {"peca_id": 1, "tipo": "comum", "descricao": "Camisetas", "preco": 28.0, "prazo_dias": 2},
    {"peca_id": 2, "tipo": "delicada", "descricao": "Vestido de festa", "preco": 25.0, "prazo_dias": 5}
  ]
}
```

## Erros

| Exceção | HTTP | Quando acontece |
|---|---|---|
| `NaoEncontradoError` | 404 | pedido ou peça com id inexistente |
| `ConflitoError` | 409 | comanda repetida; status fora da ordem; entregar antes de pronto; mexer em peças ou apagar pedido que já saiu de "recebido" |
| `DadoInvalidoError` | 422 | tamanho/tecido inválido, quantidade fora do limite, telefone ou comanda inválidos, status inexistente, prazo de pedido sem peças |
| erro do Pydantic | 422 | campo faltando ou com tipo errado na requisição |

A tradução fica em `app/routes/erros.py`. Nenhuma regra de negócio termina em 500.

## Requisitos de POO — onde estão

1. **Classe abstrata:** `Peca(ABC)` e `Repositorio(ABC)`; testes `test_peca_abstrata_nao_pode_ser_instanciada` e `test_repositorio_abstrato_nao_pode_ser_instanciado`.
2. **Herança:** `PecaComum`, `Edredom` e `Delicada` chamam `super().__init__()`.
3. **Polimorfismo:** `Pedido.valor_total()` e `prazo_dias()` chamam `p.preco()` e `p.prazo_dias()` para qualquer peça; a criação usa o dicionário `TIPOS_PECA`, sem if/elif.
4. **Encapsulamento:** atributos `_protegidos` com `@property` e setters que validam; `status` não tem setter.
5. **Composição:** `Pedido` guarda a lista de `Peca` e calcula a partir dela.
6. **Exceções próprias:** `app/models/excecoes.py`.
7. **Persistência:** `RepositorioJson` grava em `app/data/pedidos.json` (troca atômica do arquivo).
8. **Rotas:** 10 rotas, com filtro e rota de cálculo.
9. **Validação:** Pydantic para o formato (`schemas.py`), models para a regra.
10. **Testes:** 46 testes com pytest.
