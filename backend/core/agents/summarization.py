from transformers import pipeline

# Load summarization model once (efficient for repeated use)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Derive tokenizer limits and helper to chunk by tokens
tokenizer = summarizer.tokenizer
try:
    model_max = int(getattr(tokenizer, "model_max_length", 1024))
    if model_max is None or model_max > 100000:
        model_max = 1024
except Exception:
    model_max = 1024
safe_input_tokens = max(256, model_max - 128)

def _chunk_by_tokens(text: str):
    ids = tokenizer.encode(text, add_special_tokens=False)
    if not ids:
        return []
    chunks = []
    for i in range(0, len(ids), safe_input_tokens):
        seg = ids[i:i + safe_input_tokens]
        chunks.append(tokenizer.decode(seg, skip_special_tokens=True))
    return [c for c in chunks if c.strip()]

def summarize_documents(docs, length: str = "medium"):
    if not docs:
        return "No documents found to summarize."

    # Extract and combine document content
    text = " ".join((d.get("content", "") or "").strip() for d in docs).strip()
    # Normalize whitespace
    text = " ".join(text.split())
    if not text:
        return "No valid content found for summarization."

    # Define target summary lengths in NEW tokens (decoder side)
    # These do not depend on input length
    new_tok_map = {"short": (60, 110), "medium": (120, 180), "long": (200, 260)}
    min_new, max_new = new_tok_map.get(length, (120, 180))
    # Hard caps
    max_new = min(max_new, 300)
    min_new = max(16, min(min_new, max_new))

    # Chunk text according to tokenizer max length
    text_chunks = _chunk_by_tokens(text)
    if not text_chunks:
        return "No valid content found for summarization."

    summaries = []
    try:
        for i, chunk in enumerate(text_chunks):
            print(f"[SummarizationAgent] Summarizing chunk {i+1}/{len(text_chunks)}...")
            # Choose decoding params
            num_beams = 3 if length in ("medium", "long") else 4
            max_time = 20.0 if length in ("medium", "long") else 15.0

            try:
                result = summarizer(
                    chunk,
                    max_new_tokens=max_new,
                    min_new_tokens=min_new,
                    do_sample=False,
                    num_beams=num_beams,
                    no_repeat_ngram_size=3,
                    length_penalty=1.0,
                    early_stopping=True,
                    clean_up_tokenization_spaces=True,
                    max_time=max_time
                )[0]["summary_text"]
                summaries.append(result)
            except Exception as gen_err:
                print(f"[SummarizationAgent] Error on chunk {i+1}: {gen_err}")
                continue

        # Combine and re-summarize if multiple chunks
        if len(summaries) > 1:
            combined_text = " ".join(summaries)
            # Slightly higher allowance on the final pass for coherence
            final_min_new = max(min_new, 120 if length != "short" else min_new)
            final_max_new = min(max_new + 40, 340)
            num_beams = 3 if length in ("medium", "long") else 4
            max_time = 25.0 if length in ("medium", "long") else 15.0
            final_summary = summarizer(
                combined_text,
                max_new_tokens=final_max_new,
                min_new_tokens=final_min_new,
                do_sample=False,
                num_beams=num_beams,
                no_repeat_ngram_size=3,
                length_penalty=1.0,
                early_stopping=True,
                clean_up_tokenization_spaces=True,
                max_time=max_time
            )[0]["summary_text"]
            return final_summary.strip()

        return summaries[0].strip() if summaries else "No summary generated."

    except Exception as e:
        print(f"[SummarizationAgent] Error: {e}")
        return "Summarization failed due to an internal error."
