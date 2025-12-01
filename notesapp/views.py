from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from notesapp.models import Note
from notesapp.serializers import NoteSerializer
from notesapp.permissions import IsAdmin , IsAdminOrOwner

class NoteCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = NoteSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotesListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        notes = Note.objects.all()
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class NoteEditView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def patch(self, request, pk):
        try:
            note = Note.objects.get(pk=pk)
            print(note)
        except Note.DoesNotExist:
            return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, note)

        serializer = NoteSerializer(note, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
      
class NoteDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, pk):
        try:
            note = Note.objects.get(pk=pk)
        except Note.DoesNotExist:
            return Response({"error": "Note not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, note)  # admin or owner only

        note.delete()
        return Response({"message": "Note deleted successfully"}, status=status.HTTP_204_NO_CONTENT)