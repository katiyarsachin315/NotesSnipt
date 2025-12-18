from django.db import models
from accounts.models import CustomUser
from django.db.models import Q

class Note(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    content = models.TextField()
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'user'],
                condition=Q(is_deleted=False),
                name='unique_active_note_title_per_user'
            )
        ]

    def __str__(self):
        return self.title
