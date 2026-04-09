from django.urls import path
from .views import (
    ChatRoomListView,
    CreateChatRoomView,
    GetChatUsersView,
    MessageListView,
    SendMessageView,
    MarkMessagesReadView,
    GetUnreadCountView
)

urlpatterns = [
    # Chat rooms
    path('rooms/', ChatRoomListView.as_view(), name='chat-room-list'),
    path('rooms/create/', CreateChatRoomView.as_view(), name='create-chat-room'),
    path('rooms/<int:room_id>/messages/', MessageListView.as_view(), name='message-list'),
    path('rooms/<int:room_id>/messages/send/', SendMessageView.as_view(), name='send-message'),
    path('rooms/<int:room_id>/mark-read/', MarkMessagesReadView.as_view(), name='mark-read'),
    
    # Users
    path('users/', GetChatUsersView.as_view(), name='chat-users'),
    
    # Unread count
    path('unread-count/', GetUnreadCountView.as_view(), name='unread-count'),
]