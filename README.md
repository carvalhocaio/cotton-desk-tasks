# cotton-desk-tasks

Painel operacional de uma trading de algodão, construído sobre o Task
Framework nativo do Django 6 (via
[`django-tasks-db`](https://pypi.org/project/django-tasks-db/)), como
projeto de estudo do framework — cobrindo resumo de laudos HVI, relatórios
de safra, confirmação de contratos e extração de dados estruturados via
[PydanticAI](https://ai.pydantic.dev/) + Gemini.

## Cenário

O Cotton Desk recebe laudos HVI do laboratório, fecha contratos com
compradores e precisa manter os índices de preço de referência (ICE,
CEPEA) atualizados diariamente. Cada uma dessas operações dispara um
processamento assíncrono — resumir um laudo, consolidar uma safra, gerar
a confirmação textual de um contrato — que não deve bloquear a resposta
ao usuário. O painel em `/dashboard/` mostra essas tasks em tempo real
(via polling), transitando entre os estados `READY` → `RUNNING` →
`SUCCESSFUL`/`FAILED`.

## Decisões de arquitetura

As decisões de maior impacto estão registradas em [`ADR.md`](ADR.md):

| ADR | Decisão                                                       |
|-----|---------------------------------------------------------------|
| 001 | Django Tasks Framework (`django-tasks-db`) em vez de Celery   |
| 002 | PydanticAI + Gemini para extração estruturada de confirmações |
| 003 | Polling simples no painel, em vez de WebSocket                |

Cada ADR documenta não só a decisão, mas os trade-offs vividos na prática
e o gatilho concreto que justificaria revisá-la.

## Estrutura

```
.
├── config/                          # settings, urls, wsgi/asgi do projeto Django
├── desk/
│   ├── models.py                    # Fardo, LaudoHVI, Contrato, IndicePreco
│   ├── domain.py                    # HVIParametros — validação de negócio, sem Django
│   ├── tasks.py                     # tasks assíncronas (@task), uma por fila
│   ├── extracao.py                  # agente PydanticAI para extração de confirmações
│   ├── views.py                     # endpoints HTTP + painel
│   ├── urls.py
│   ├── templates/desk/dashboard.html
│   ├── management/commands/registrar_preco.py
│   └── tests/
├── ADR.md                           # decisões de arquitetura registradas
├── manage.py
└── main.py
```

`domain.py` não depende de Django nem de banco — a validação dos
parâmetros HVI (micronaire, comprimento, resistência, uniformidade) é um
value object puro, testável isoladamente. `LaudoHVI.to_dominio()` é o
único ponto de conversão entre o dado bruto salvo e a regra de negócio.

## Filas de tasks

| Fila           | Task                       | Prioridade | O que faz                                                               |
|----------------|----------------------------|------------|-------------------------------------------------------------------------|
| `laudos`       | `resumir_laudo`            | 50         | Resume um laudo HVI a partir dos parâmetros validados                   |
| `relatorios`   | `gerar_relatorio_safra`    | -10        | Consolida quantos laudos de uma safra são comercialmente válidos        |
| `confirmacoes` | `confirmar_contrato`       | 50         | Gera a confirmação textual de um contrato fechado                       |
| `confirmacoes` | `extrair_confirmacao`      | 30         | Extrai dados de um texto livre via IA e cria o contrato                 |
| `precos`       | `registrar_leitura_indice` | 0          | Persiste uma leitura de índice de preço                                 |
| `demo`         | `tarefa_de_demonstracao`   | 0          | Task artificialmente lenta, só para exibir o estado `RUNNING` no painel |

## Setup

```bash
uv sync
echo "GOOGLE_API_KEY=sua-chave-aqui" >> .env
uv run python manage.py migrate
```

A chave é lida de `GOOGLE_API_KEY` e usada pelo agente PydanticAI em
`desk/extracao.py`. Sem ela, apenas os fluxos que chamam a API do Gemini
de fato (`extrair_confirmacao`) ficam indisponíveis — o restante do
projeto funciona normalmente.

## Makefile

Os comandos de instalação, execução, testes e qualidade abaixo também
estão disponíveis como atalhos via `make` (`make help` lista todos):

```bash
make install    # uv sync
make migrate    # manage.py migrate
make run        # manage.py runserver
make worker     # manage.py db_worker
make test       # suíte de testes
make lint       # ruff check
make format     # ruff format
make ci         # lint + format-check + pip-audit + testes (mesmo pipeline da CI)
```

## Uso

```bash
# servidor de desenvolvimento
uv run python manage.py runserver

# worker que processa as filas (outro terminal)
uv run python manage.py db_worker

# registrar uma leitura de índice de preço (ex.: via cron)
uv run python manage.py registrar_preco ICE-CT2 82.35 2026-04-28
```

Com os dois processos no ar, o painel fica em `http://localhost:8000/dashboard/`,
com botões de demonstração para enfileirar cada tipo de task e acompanhar
a transição de estado. O worker aceita `--interval` para ajustar a
frequência de poll do próprio banco (afeta só a visibilidade no painel,
não a duração da execução da task).

## Testes

```bash
uv run pytest
```

A suíte não depende de rede: o teste de extração (`test_extrair_confirmacao.py`)
usa `Agent.override()` com `TestModel` do PydanticAI, e os testes de task
usam os backends de teste do Django Tasks Framework (`ImmediateBackend`)
ou o `DatabaseBackend` diretamente quando o comportamento do worker real
importa (`test_worker_real.py`).

## Qualidade de código

Lint e formatação com [Ruff](https://docs.astral.sh/ruff/):

```bash
uv run ruff check              # lint
uv run ruff check --fix        # lint + correções automáticas
uv run ruff format             # formatação
```

Ou via `make lint`, `make lint-fix`, `make format`, `make format-check`.
`make ci` roda o mesmo pipeline usado no GitHub Actions.

O [GitHub Actions](.github/workflows/ci.yml) roda `ruff check`,
`ruff format --check`, um scan de dependências (`pip-audit`) e a suíte de
testes a cada push/PR na `main`.

## Segurança

- **`GOOGLE_API_KEY` fica em `.env`, fora do controle de versão** (ver
  `.gitignore`). O `Agent` do PydanticAI é criado com `defer_model_check=True`
  para que a ausência da chave não quebre a suíte inteira só por importar
  o módulo.
- **Falha de correspondência é tratada como falha real, não mascarada.**
  Se `extrair_confirmacao` recebe um código de fardo que não existe, a
  task falha com `Fardo.DoesNotExist` em vez de tentar um fallback
  silencioso — um LLM pode alucinar ou errar o código, e isso precisa
  ficar visível para triagem humana.
- **O texto de entrada de `extrair_confirmacao` é processado pela API do
  Google Gemini** (serviço externo). Não use dados reais de contratos,
  clientes ou preços na demonstração — use exemplos fictícios.

## Limitações conhecidas

- **Sem agendamento embutido.** `registrar_preco` precisa de um cron
  externo chamando o management command; o Tasks Framework nativo não
  tem equivalente ao Celery Beat.
- **Transições de estado mais curtas que o intervalo de poll do painel
  (1,5s) são difíceis de observar.** `tarefa_de_demonstracao` existe só
  para tornar visível o estado `RUNNING`, que nas tasks reais passa rápido
  demais.
- **`ImmediateBackend` não suporta `get_result()` por id** — consultar o
  status de uma task após enfileirada exige o `DatabaseBackend`.
- **Sem correspondência fuzzy de fardo.** Se `extrair_confirmacao` receber
  um código de fardo incorreto, a task simplesmente falha; não há
  sugestão automática do fardo mais próximo.

## Créditos

Projeto de estudo do Django Tasks Framework (`django-tasks-db`) e do
PydanticAI, aplicados ao domínio de comércio de algodão.
