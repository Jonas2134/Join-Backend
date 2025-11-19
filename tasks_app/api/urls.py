from django.urls import path

from .views import TaskListCreateView

urlpatterns = [
    path('columns/<int:column_pk>/tasks/', TaskListCreateView.as_view(), name='task-list-create'),
]
