from django.urls import path

from .views import AllBoardsView

urlpatterns = [
    path('all-boards/', AllBoardsView.as_view(), name='all_boards'),
]
