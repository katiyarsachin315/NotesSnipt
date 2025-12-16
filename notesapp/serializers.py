from rest_framework import serializers
from notesapp.models import Note

class NoteSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(
        max_length=500, required=False, allow_blank=True
    )
    content = serializers.CharField()
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)

    def validate_title(self, value):
        queryset = Note.objects.filter(title=value, is_deleted=False)

        # Update ke case me current instance exclude
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                "Note with this title already exists."
            )

        return value

    def create(self, validated_data):
        return Note.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get(
            'description', instance.description
        )
        instance.content = validated_data.get('content', instance.content)
        instance.save()
        return instance
