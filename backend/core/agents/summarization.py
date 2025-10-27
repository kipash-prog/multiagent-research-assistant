from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_documents(docs, length: str = "medium"):
    """
    Summarize a list of document dicts into a single summary string.
    """
    if not docs:
        return "No documents found to summarize."

    text = " ".join(d["content"] for d in docs if d.get("content"))
    if len(text.strip()) == 0:
        return "No valid content found for summarization."

    length_map = {"short": (50, 150), "medium": (150, 300), "long": (300, 500)}
    min_len, max_len = length_map.get(length, (150, 300))

    try:
        summary = summarizer(
            text, max_length=max_len, min_length=min_len, do_sample=False
        )[0]["summary_text"]
        return summary
    except Exception as e:
        print(f"[SummarizationAgent] Error: {e}")
        return "Summarization failed due to an internal error."
