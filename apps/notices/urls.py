from django.urls import path
from .views import NoticeListView, NoticeCreateView, NoticeDeleteView, NoticeUpdateView

urlpatterns = [
    path('', NoticeListView.as_view(), name='notice-list'),
    path('create/', NoticeCreateView.as_view(), name='notice-create'),
    path('<int:pk>/', NoticeDeleteView.as_view(), name='notice-delete'),
    path('<int:pk>/update/', NoticeUpdateView.as_view(), name='notice-update'),
]