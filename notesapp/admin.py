from django.contrib import admin
from notesapp.models import Note

# Register your models here.
class NoteAdmin(admin.ModelAdmin):
    model = Note
    list_display = ['id', 'title', 'user', 'created_at', 'updated_at', 'is_deleted']
    search_fields = ['title', 'content', 'description']
    list_filter = ['created_at', 'updated_at', 'is_deleted']

admin.site.register(Note, NoteAdmin)


