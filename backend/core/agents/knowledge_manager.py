from ..models import Document, Summary

def store_documents(query_obj, gathered_docs):
    """
    Saves gathered documents under the given Query object.
    """
    for d in gathered_docs:
        Document.objects.create(
            query=query_obj,
            source=d.get("source", "Unknown"),
            url=d.get("url", ""),
            content=d.get("content", ""),
        )

def store_summary(query_obj, summary_text, summary_type="medium"):
    """
    Saves summary text as a Summary linked to the Query.
    """
    Summary.objects.create(
        query=query_obj,
        summary_text=summary_text,
        summary_type=summary_type,
    )
