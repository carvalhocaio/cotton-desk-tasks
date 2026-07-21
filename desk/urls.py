from django.urls import path

from desk import views

urlpatterns = [
    path("laudos/<int:laudo_id>/resumir/", views.resumir_laudo, name="resumir_laudo"),
    path("tasks/<str:task_id>/", views.status_da_task, name="status_da_task"),
    path("checkout/", views.checkout, name="checkout"),
    path("laudos/upload-lote/", views.upload_lote_laudos, name="upload_lote_laudos"),
    path("dashboard/tasks.json", views.tasks_json, name="tasks_json"),
    path("dashboard/limpar/", views.limpar_tasks, name="limpar_tasks"),
    path("dashboard/relatorio-teste/", views.relatorio_teste, name="relatorio_teste"),
    path("dashboard/preco-teste/", views.preco_teste, name="preco_teste"),
    path("dashboard/contrato-teste/", views.contrato_teste, name="contrato_teste"),
    path("dashboard/demo-lenta/", views.demo_lenta, name="demo_lenta"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
