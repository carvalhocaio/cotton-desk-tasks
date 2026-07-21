# ADR 001: Django Tasks (com django-tasks-db) em vez de Celery

## Status
Aceito - para fins de aprendizado. Ver seção "Gatilho para revisão" antes de usar em produção.

## Contexto
O `cotton-desk-tasks` precisava de processamento assíncrono para três tipos de
trabalho: resumo de laudos (latência importa), relatórios de safra
(agregação, pode esperar) e confirmação de contratos (precisa esperar o
commit da transação). As opções consideradas foram o Task Framework nativo
do Django 6.0 (via `django-tasks-db` como backend de persistência) e Celery.

## Decisão
Usamos o Tasks Framework nativo, com `django-tasks-db.DatabaseBackend`.

## Motivos
- **Objetivo do projeto era aprender o framework em si** - trocar por Celery descaracterizaria o propósito do repositório.
- **Zero infraestrutura extra.** `django-tasks-db` usa o mesmo banco Postgres que o resto da aplicação já usa; não precisa de Redis/RabbitMQ rodando em paralelo. Para um projeto de porte pequeno/médio, isso é uma dependência operacional a menos.
- **API nativa do Django.** `@task`, `.enqueue()`, `TaskResult` - sem decorators de terceiros, sem `celery.py` separado, sem configuração de broker.

## Trade-offs conhecidos (vividos neste projeto, não hipotéticos)
- **Sem agendamento embutido**. Celery tem Celery Beat nativo; aqui precisamos de cron externo chamando um management command (`registrar_preco`). Documentado, mas é uma peça a mais para manter.
- **`django-task-db` é um pacote comunitário**, não faz parte do core do Django - os backends embutidos (`ImmediateBackend`, `DummyBackend`) são explicitamente não recomendados para produção pela documentação oficial. Celery tem décadas de battle-testing em produção; `django-tasks-db` não.
- **`ImmediateBackend` não suporta `get_result()` por ID** - descoberto testes de "a task roda" (podem usar `ImmediateBackend`) de testes de "consultar status depois" (precisam mockar o `TaskResult` ou, no caso do gotcha do worker real, rodar `DatabaseBackend` com `transaction=True`).
- **Retry, rate limiting e monitoramento** são bem mais maduros no ecossistema Celery (Flower, retry com backoff configurável.) O Tasks Framework nativo ainda é recente; menos ferramentas de observabilidade prontas.

## Gatilho para revisão
Se este projeto (ou um sucessor dele) for para produção real com volume
significativo de tasks, ou precisar de agendamento recorrente complexo,
rety sofisticado, ou monitoramento tipo Flower - reavaliar Celery nesse
momento, não antes. Trocar de backend agora, sem essas pressões reais, seria otimização prematura.

---

# ADR 002: PydanticAI + Gemini para extração estruturada de confirmações

## Status
Aceito.

## Contexto
A fase atual precisava transformar texto livre (uma confirmação de contrato
recebida por e-mail, por exemplo) em dados estruturados que pudessem criar
um `Contrato` de verdade. As opções consideradas foram PydanticAI e LangChain
com saída estruturada via `with_structured_output`.

## Decisão
Usamos PydanticAI, com `Agent(output_type=DadosConfirmacao, ...)` e o modelo
`google:gemini-2.5-flash`.

## Motivos
- **A validação de schema é o ponto central do PydanticAI** - o `output_type` é um `BaseModel` do Pydantic, e a lib trata a validação/retry de schema como parte do core, não como um recurso anexado.
- **`TestModel` + `Agent.override()` tornam o teste determinístico e offline** - nenhum teste da suíte precisa de `GOOGLE_API_KEY` nem toca rede.

## Trade-offs conhecidos (vividos neste projeto)
- **Checagem de API key eager na criação do `Agent`.** Só *importar* o módulo sem `GOOGLE_API_KEY` no ambiente quebraria a suíte inteira, mesmo em testes que nunca chamam a API de verdade. Resolvido com `defer_model_check=True`, mas é uma pegadinha que só apareceu testando, não estava documentada com destaque.
- **Falha de correspondência (`fardo_codigo` que não existe) é tratada como falha real da task** (`Fardo.DoesNotExist`), não como retry silencioso ou fallback. Isso é proposital — um LLM pode alucinar ou errar o código do fardo, e mascarar isso deixaria o erro passar sem rastro. O custo é que, em produção, cada falha dessas precisas de triagem humana (não há correção automática de código de fardo ainda).
- **`extrair_confirmacao` compartilha a fila `confirmacoes` com `confirmar_contrato`**, mas com prioridade menor (30 vs 50) — uma chamada de LLM é ordens de magnitude mais lenta que uma leitura de banco. Se o volume de confirmações via IA crescer muito, isso pode competir por worker com as confirmações diretas; nesse ponto, uma fila dedicada (`extracao-ia`) seria a próxima decisão a revisitar.

## Gatilho para revisão
Se o volume de extrações via LLM crescer o suficiente para competir de
verdade com `confirm_contrato` pela fila `confirmacoes`, separar numa fila
própria. Se a taxa de `Fardo.DoesNotExists` se mostrar alta, na prática,
considerar uma etapa de correspondência fuzzy (ex.: sugerir o fardo mais
próximo) antes de falhar a task.