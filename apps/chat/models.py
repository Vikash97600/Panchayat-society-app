from django.db import models
from apps.accounts.models import CustomUser


class ChatRoom(models.Model):
    """
    Chat room between a Resident and Committee Member.
    One room per Resident ↔ Committee pair.
    """
    resident = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='chat_rooms_as_resident',
        limit_choices_to={'role': 'resident'}
    )
    committee = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='chat_rooms_as_committee',
        limit_choices_to={'role': 'committee'}
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_rooms'
        unique_together = ('resident', 'committee')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat: {self.resident.email} ↔ {self.committee.email}"

    def get_other_user(self, user):
        """Get the other participant in the chat."""
        if user == self.resident:
            return self.committee
        elif user == self.committee:
            return self.resident
        return None


class Message(models.Model):
    """
    Chat message in a chat room.
    """
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender.email} at {self.created_at}"