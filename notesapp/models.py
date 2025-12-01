from django.db import models
from accounts.models import CustomUser

# Create your models here.
class Note(models.Model):
    title = models.CharField(max_length=100)  # Title jo mandatory hoga
    description = models.TextField(blank=True, null=True)  # Optional field
    content = models.TextField()  # Main content jo mandatory hoga
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # User ke saath relation
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)  # Soft delete

    def __str__(self):
        return self.title