from rest_framework import serializers
from .models import Query, Document, Summary

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "source", "url", "content", "fetched_at"]

class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = ["id", "summary_text", "summary_type", "created_at"]

class QuerySerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)
    summaries = SummarySerializer(many=True, read_only=True)
    class Meta:
        model = Query
        fields = ["id", "query_text", "created_at", "documents", "summaries"]
