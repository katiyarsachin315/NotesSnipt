from django.urls import path
from notesapp.views import *

urlpatterns = [
    path('getnotes/', NotesListView.as_view(), name='get-notes'),
    path('create/', NoteCreateView.as_view(), name='note-create'),
    path('update/<pk>/', NoteEditView.as_view(), name='note-update'),
    path('delete/<pk>/', NoteDeleteView.as_view(), name='note-delete'),
    path('admin/note/<int:note_id>/update/', AdminUpdateNoteView.as_view(), name='admin-update-note'),
    path('admin/note/<int:note_id>/delete/', AdminDeleteNoteView.as_view(), name='admin-delete-note'),
    path('admin/note/<int:note_id>/restore/', AdminRestoreNoteView.as_view(), name='admin-restore-note'),
]