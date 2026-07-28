from rest_framework import serializers

from .models import Document


class DocumentUploadSerializer(serializers.Serializer):

    file = serializers.FileField()


class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = "__all__"