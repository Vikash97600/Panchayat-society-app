from rest_framework import serializers
from .models import ChatRoom, Message
from apps.accounts.serializers import UserProfileSerializer


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True)
    is_me = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'content', 'created_at', 'is_read', 'sender', 'sender_name', 'sender_role', 'is_me']
        read_only_fields = ['id', 'created_at', 'is_read', 'sender', 'sender_name', 'sender_role']

    def get_is_me(self, obj):
        """Check if the message is sent by the current user."""
        request = self.context.get('request')
        if request and request.user:
            return obj.sender.id == request.user.id
        return False


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for chat rooms."""
    resident_name = serializers.CharField(source='resident.get_full_name', read_only=True)
    committee_name = serializers.CharField(source='committee.get_full_name', read_only=True)
    resident_info = UserProfileSerializer(source='resident', read_only=True)
    committee_info = UserProfileSerializer(source='committee', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'resident', 'committee', 'created_at', 'updated_at',
            'resident_name', 'committee_name', 'resident_info', 'committee_info',
            'last_message', 'unread_count', 'other_user'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        """Get the last message in the room."""
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(last_msg, context=self.context).data
        return None

    def get_unread_count(self, obj):
        """Get count of unread messages for current user."""
        request = self.context.get('request')
        if request and request.user:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0

    def get_other_user(self, obj):
        """Get the other participant in the chat."""
        request = self.context.get('request')
        if request and request.user:
            other = obj.get_other_user(request.user)
            if other:
                return {
                    'id': other.id,
                    'name': other.get_full_name(),
                    'role': other.role,
                    'email': other.email
                }
        return None


class CreateMessageSerializer(serializers.ModelSerializer):
    """Serializer for creating messages."""

    class Meta:
        model = Message
        fields = ['content']

    def validate_content(self, value):
        """Validate message content."""
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        if len(value) > 2000:
            raise serializers.ValidationError("Message content cannot exceed 2000 characters")
        return value.strip()


class CreateChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for creating chat rooms."""
    other_user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ChatRoom
        fields = ['other_user_id']

    def validate_other_user_id(self, value):
        """Validate the other user exists and is of appropriate role."""
        from apps.accounts.models import CustomUser
        from django.core.exceptions import ValidationError
        
        try:
            user = CustomUser.objects.get(id=value, is_active=True)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User not found")
        
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context not available")
        
        current_user = request.user
        
        # Validate role combination
        if current_user.role == 'resident' and user.role != 'committee':
            raise serializers.ValidationError("Residents can only chat with committee members")
        
        if current_user.role == 'committee' and user.role != 'resident':
            raise serializers.ValidationError("Committee members can only chat with residents")
        
        return value

    def create(self, validated_data):
        """Create or get existing chat room."""
        from apps.accounts.models import CustomUser
        
        current_user = self.context.get('request').user
        other_user = CustomUser.objects.get(id=validated_data['other_user_id'])
        
        # Determine who is resident and who is committee
        if current_user.role == 'resident':
            resident = current_user
            committee = other_user
        else:
            resident = other_user
            committee = current_user
        
        # Check if room already exists
        room, created = ChatRoom.objects.get_or_create(
            resident=resident,
            committee=committee
        )
        
        return room