from django.http import JsonResponse
from django.tasks import TaskResultStatus, default_task_backend
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from desk.tasks import resumir_laudo as tarefa_resumir_laudo


@csrf_exempt
@require_POST
def resumir_laudo(request, laudo_id):
    """Enfileira o resumo de um laudo HVI e devolve o id da task."""
    resultado = tarefa_resumir_laudo.enqueue(laudo_id)
    return JsonResponse({"task_id": str(resultado.id)}, status=202)


@require_GET
def status_da_task(request, task_id):
    """Consulta o status de uma task já enfileirada."""
    resultado = default_task_backend.get_result(task_id)
    resultado.refresh()

    if resultado.status == TaskResultStatus.SUCCESSFUL:
        return JsonResponse({"status": "concluida", "resultado": resultado.return_value})

    if resultado.status == TaskResultStatus.FAILED:
        erro = resultado.errors[0].exception_class_path
        return JsonResponse({"status": "falhou", "erro": erro}, status=422)

    return JsonResponse({"status": "pendente"})
