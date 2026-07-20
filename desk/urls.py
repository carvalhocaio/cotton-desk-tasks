from django.urls import path

from desk import views

urlpatterns = [
    path("laudos/<int:laudo_id>/resumir/", views.resumir_laudo, name="resumir_laudo"),
    path("tasks/<str:task_id>/", views.status_da_task, name="status_da_task"),
    path("checkout/", views.checkout, name="checkout"),
]
