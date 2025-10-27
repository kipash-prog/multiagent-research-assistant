from django.db import models

class Query(models.Model):
    query_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Query {self.id}: {self.query_text[:50]}"

class Document(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name="documents")
    source = models.CharField(max_length=255, blank=True)
    url = models.URLField(blank=True)
    content = models.TextField()
    fetched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Doc {self.id} from {self.source}"

class Summary(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name="summaries")
    summary_text = models.TextField()
    summary_type = models.CharField(max_length=50, default="medium")  # short/medium/long
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary {self.id} ({self.summary_type})"
