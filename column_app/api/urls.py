from django.urls import path

from .views import ColumnListCreateView, ColumnDetailViewSet

column_detail = ColumnDetailViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "delete": "destroy",
})

urlpatterns = [
    path('boards/<int:board_pk>/columns/', ColumnListCreateView.as_view(), name='column-list-create'),
    path('columns/<int:column_pk>/', column_detail, name='column-detail'),
]

