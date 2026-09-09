from django.urls import path

from desk import views

urlpatterns = [
    path(
        "reports/<int:report_id>/summarize/",
        views.summarize_report,
        name="summarize_report",
    ),
    path("tasks/<str:task_id>/", views.task_status, name="task_status"),
    path("checkout/", views.checkout, name="checkout"),
    path(
        "reports/upload-batch/", views.upload_report_batch, name="upload_report_batch"
    ),
    path("dashboard/tasks.json", views.tasks_json, name="tasks_json"),
    path("dashboard/clear/", views.clear_tasks, name="clear_tasks"),
    path("dashboard/demo-report/", views.demo_report, name="demo_report"),
    path("dashboard/demo-price/", views.demo_price, name="demo_price"),
    path("dashboard/demo-contract/", views.demo_contract, name="demo_contract"),
    path("dashboard/demo-slow/", views.demo_slow, name="demo_slow"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
