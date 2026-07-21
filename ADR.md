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
- **Sem agendamento embutido**. Celery tem Celery Beat nativo; aqui precisamos de cron externo chamando um management command (`registrar_preco`). Documentado, mas é uma peça a mais pra manter.
- **`django-task-db` é um pacote comunitário**, não faz parte do core do Django - os backends embutidos (`ImmediateBackend`, `DummyBackend`) são explicitamente não recomendados para produção pela documentação oficial. Celery tem décadas de battle-testing em produção; `django-tasks-db` não.
- **`ImmediateBackend` não suporta `get_result()` por ID** - descoberto testes de "a task roda" (podem usar `ImmediateBackend`) de testes de "consultar status depois" (precisam mockar o `TaskResult` ou, no caso do gotcha do worker real, rodar `DatabaseBackend` com `transaction=True`).
- **Retry, rate limiting e monitoramento** são bem mais maduros no ecossistema Celery (Flower, retry com backoff configurável.) O Tasks Framework nativo ainda é recente; menos ferramentas de observabilidade prontas.

## Gatilho para revisão
Se este projeto (ou um sucessor dele) for para produção real com volume
significativo de tasks, ou precisar de agendamento recorrente complexo,
rety sofisticado, ou monitoramento tipo Flower - reavaliar Celery nesse
momento, não antes. Trocar de backend agora, sem essas pressões reais, seria otimização prematura.
