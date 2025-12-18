from rest_framework import serializers
from notesapp.models import Note

class NoteSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=100)
    description = serializers.CharField(
        max_length=500, required=False, allow_blank=True
    )
    content = serializers.CharField()
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)

    def validate_title(self, value):
        request = self.context.get('request')
        user = request.user if request else None

        queryset = Note.objects.filter(
            title=value,
            user=user,
            is_deleted=False
        )

        # Update case → exclude current note
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise serializers.ValidationError(
                "You already have a note with this title."
            )

        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return Note.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get(
            'description', instance.description
        )
        instance.content = validated_data.get('content', instance.content)
        instance.save()
        return instance
