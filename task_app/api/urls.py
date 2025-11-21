from django.urls import path

from .views import TaskListCreateView, TaskDetailViewSet

task_detail = TaskDetailViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "delete": "destroy",
})

urlpatterns = [
    path('columns/<int:column_pk>/tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:task_pk>/', task_detail),
]
