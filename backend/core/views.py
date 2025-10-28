from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import QuerySerializer, DocumentSerializer, SummarySerializer
from .models import Query
from .agents import research_gathering, summarization, knowledge_manager
from rest_framework.generics import RetrieveAPIView, ListAPIView

class QueryView(APIView):
    """
    Accepts POST with:
    {
        "query_text": "AI in healthcare",
        "summary_type": "medium"
    }
    """

    def post(self, request):
        # ✅ 1. Get query text and fallback key
        q_text = request.data.get("query_text") or request.data.get("query") or ""
        q_text = q_text.strip()

        summary_type = request.data.get("summary_type", "medium")

        if not q_text:
            return Response(
                {"error": "Please provide a valid 'query_text'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # ✅ 2. Create Query record
            q_obj = Query.objects.create(query_text=q_text)

            # ✅ 3. Gather research data
            gathered = research_gathering.gather(q_text, max_sources=4)
            print(f"[QueryView] Gathered {len(gathered)} sources for query '{q_text}'")

            # ✅ 4. Store documents in knowledge manager
            knowledge_manager.store_documents(q_obj, gathered)

            # ✅ 5. Summarize
            summary_text = summarization.summarize_documents(gathered, length=summary_type)
            print(f"[QueryView] Summary generated ({summary_type})")

            # ✅ 6. Store summary
            knowledge_manager.store_summary(q_obj, summary_text, summary_type=summary_type)

            # ✅ 7. Serialize and return
            serializer = QuerySerializer(q_obj)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"[QueryView] ❌ Error processing query: {e}")
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class QueryListView(ListAPIView):
    queryset = Query.objects.all().order_by("-created_at")
    serializer_class = QuerySerializer

class QueryDetailView(RetrieveAPIView):
    queryset = Query.objects.all()
    serializer_class = QuerySerializer
