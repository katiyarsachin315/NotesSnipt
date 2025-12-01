from django.urls import path
from notesapp.views import *

urlpatterns = [
    path('getnotes/', NotesListView.as_view(), name='get-notes'),
    path('create/', NoteCreateView.as_view(), name='note-create'),
    path('update/<pk>/', NoteEditView.as_view(), name='note-update'),
    path('delete/<pk>/', NoteDeleteView.as_view(), name='note-delete'),
]