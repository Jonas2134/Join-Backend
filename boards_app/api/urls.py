from django.urls import path

from .views import BoardListCreateView, BoardDetailViewSet, ColumnCreateView, ColumnUpdateDestroyView


board_detail = BoardDetailViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "delete": "destroy",
})

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:pk>/', board_detail),
    path('boards/<int:pk>/columns/', ColumnCreateView.as_view(), name='column-create'),
    path('boards/<int:pk>/columns/<int:column_pk>/', ColumnUpdateDestroyView.as_view(), name='column-update-destroy'),
]
