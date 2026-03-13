from django.urls import path

from .views import BoardListCreateView, BoardDetailViewSet


board_detail = BoardDetailViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "delete": "destroy",
})

board_leave = BoardDetailViewSet.as_view({
    "post": "leave",
})

urlpatterns = [
    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:pk>/', board_detail, name='board-detail'),
    path('boards/<int:pk>/leave/', board_leave, name='board-leave'),
]
