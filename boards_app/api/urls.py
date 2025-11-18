from django.urls import path

from .views import BoardListCreateView, BoardDetailViewSet, ColumnCreateView


board_detail = BoardDetailViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "delete": "destroy",
})

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:pk>/', board_detail),
    path('boards/columns/', ColumnCreateView.as_view(), name='column-create'),
]
