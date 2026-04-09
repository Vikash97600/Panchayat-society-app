from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from .models import ChatRoom, Message
from .serializers import (
    ChatRoomSerializer, 
    MessageSerializer, 
    CreateMessageSerializer,
    CreateChatRoomSerializer
)


class IsChatUser(permissions.BasePermission):
    """Permission check for chat access."""
    
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and user.role in ['resident', 'committee']


class ChatRoomListView(generics.ListAPIView):
    """
    GET /api/chat/rooms/
    List all chat rooms for the logged-in user.
    """
    serializer_class = ChatRoomSerializer
    permission_classes = [IsChatUser]

    def get_queryset(self):
        user = self.request.user
        return ChatRoom.objects.filter(
            Q(resident=user) | Q(committee=user)
        ).select_related('resident', 'committee').prefetch_related('messages')


class CreateChatRoomView(generics.CreateAPIView):
    """
    POST /api/chat/rooms/create/
    Create a new chat room with another user.
    """
    serializer_class = CreateChatRoomSerializer
    permission_classes = [IsChatUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        room = serializer.save()
        
        response_serializer = ChatRoomSerializer(room, context={'request': request})
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Chat room created successfully'
        }, status=status.HTTP_201_CREATED)


class GetChatUsersView(APIView):
    """
    GET /api/chat/users/
    Get list of users that the current user can chat with.
    Residents get committee members, Committee members get residents.
    """
    permission_classes = [IsChatUser]

    def get(self, request):
        from apps.accounts.models import CustomUser
        from apps.accounts.serializers import UserProfileSerializer
        
        user = request.user
        
        if user.role == 'resident':
            # Get committee members in the same society
            users = CustomUser.objects.filter(
                role='committee',
                society=user.society,
                is_active=True,
                is_approved=True
            )
        elif user.role == 'committee':
            # Get residents in the same society
            users = CustomUser.objects.filter(
                role='resident',
                society=user.society,
                is_active=True,
                is_approved=True
            )
        else:
            return Response({
                'success': False,
                'message': 'Invalid user role'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserProfileSerializer(users, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })


class MessageListView(generics.ListAPIView):
    """
    GET /api/chat/rooms/{room_id}/messages/
    Get all messages in a chat room.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsChatUser]

    def get_queryset(self):
        room_id = self.kwargs.get('room_id')
        user = self.request.user
        
        # Validate room access
        try:
            room = ChatRoom.objects.get(
                Q(resident=user) | Q(committee=user),
                id=room_id
            )
        except ChatRoom.DoesNotExist:
            return Message.objects.none()
        
        # Mark messages as read
        Message.objects.filter(
            room=room,
            is_read=False
        ).exclude(sender=user).update(is_read=True)
        
        return room.messages.all().select_related('sender')


class SendMessageView(generics.CreateAPIView):
    """
    POST /api/chat/rooms/{room_id}/messages/
    Send a message to a chat room.
    """
    serializer_class = CreateMessageSerializer
    permission_classes = [IsChatUser]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['room_id'] = self.kwargs.get('room_id')
        return context

    def create(self, request, *args, **kwargs):
        room_id = self.kwargs.get('room_id')
        user = request.user

        # Validate room access
        try:
            room = ChatRoom.objects.get(
                Q(resident=user) | Q(committee=user),
                id=room_id
            )
        except ChatRoom.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Chat room not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CreateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create message
        message = Message.objects.create(
            room=room,
            sender=user,
            content=serializer.validated_data['content']
        )

        # Update room timestamp
        room.save()  # This updates updated_at

        response_serializer = MessageSerializer(message, context={'request': request})
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Message sent successfully'
        }, status=status.HTTP_201_CREATED)


class MarkMessagesReadView(APIView):
    """
    POST /api/chat/rooms/{room_id}/mark-read/
    Mark all messages in a room as read.
    """
    permission_classes = [IsChatUser]

    def post(self, request, room_id):
        user = request.user

        # Validate room access
        try:
            room = ChatRoom.objects.get(
                Q(resident=user) | Q(committee=user),
                id=room_id
            )
        except ChatRoom.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Chat room not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Mark unread messages as read (excluding own messages)
        updated = Message.objects.filter(
            room=room,
            is_read=False
        ).exclude(sender=user).update(is_read=True)

        return Response({
            'success': True,
            'message': f'{updated} messages marked as read'
        })


class GetUnreadCountView(APIView):
    """
    GET /api/chat/unread-count/
    Get total unread message count for current user.
    """
    permission_classes = [IsChatUser]

    def get(self, request):
        user = request.user
        
        # Get all rooms for user
        rooms = ChatRoom.objects.filter(
            Q(resident=user) | Q(committee=user)
        )
        
        # Count unread messages
        unread_count = Message.objects.filter(
            room__in=rooms,
            is_read=False
        ).exclude(sender=user).count()

        return Response({
            'success': True,
            'data': {'unread_count': unread_count}
        })