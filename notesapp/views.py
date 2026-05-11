from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from notesapp.models import Note
from notesapp.serializers import NoteSerializer, AdminNoteUpdateSerializer
from notesapp.permissions import IsAdminOnly, IsAdminOrOwner
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from accounts.models import CustomUser

class NoteCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = NoteSerializer(
            data=request.data,
            context={'request': request}   # ✅ FIX
        )

        if serializer.is_valid():
            serializer.save()  # 👈 user already set in serializer
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class NotesListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notes = Note.objects.filter(is_deleted=False)
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NoteEditView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def put(self, request, pk):
        note = get_object_or_404(Note, pk=pk, is_deleted=False)

        self.check_object_permissions(request, note)

        serializer = NoteSerializer(
            note,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NoteDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def delete(self, request, pk):
        try:
            note = Note.objects.get(
                pk=pk,
                is_deleted=False
            )
        except Note.DoesNotExist:
            return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, note)  # admin or owner only

        # 🔥 SOFT DELETE
        note.is_deleted = True
        note.save()
        return Response({"message": "Note deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    
    
#Admin Operations on Notes


class AdminUpdateNoteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def put(self, request, note_id):
        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return Response({"error": "Note not found"}, status=404)

        serializer = AdminNoteUpdateSerializer(note, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Note updated successfully"})

        return Response(serializer.errors, status=400)
    

class AdminDeleteNoteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def delete(self, request, note_id):
        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return Response({"error": "Note not found"}, status=404)

        note.delete()   # 🔥 HARD DELETE

        return Response({"message": "Note permanently deleted"})
    

class AdminRestoreNoteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def patch(self, request, note_id):

        try:
            note = Note.objects.get(
                pk=note_id,
                is_deleted=True
            )

        except Note.DoesNotExist:
            return Response(
                {"error": "Note not found"},
                status=404
            )

        # 🔥 Restore note
        note.is_deleted = False
        note.save()

        return Response({
            "message": "Note restored successfully"
        })