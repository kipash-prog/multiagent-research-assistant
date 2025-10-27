from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import QuerySerializer, DocumentSerializer, SummarySerializer
from .models import Query
from .agents import research_gathering, summarization, knowledge_manager

class QueryView(APIView):
    def post(self, request):
        q_text = request.data.get("query_text", "").strip()
        summary_type = request.data.get("summary_type", "medium")
        if not q_text:
            return Response({"error": "query_text is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1) Create Query record (interaction agent)
        q_obj = Query.objects.create(query_text=q_text)

        # 2) Research Gathering Agent: fetch online sources (best-effort)
        gathered = research_gathering.gather(q_text, max_sources=4)

        # 3) Store Documents (Knowledge Manager)
        knowledge_manager.store_documents(q_obj, gathered)

        # 4) Summarization & Analysis Agent
        summary_text = summarization.summarize_documents(gathered, length=summary_type)

        # 5) Store Summary (Knowledge Manager)
        knowledge_manager.store_summary(q_obj, summary_text, summary_type=summary_type)

        # 6) Return serialized query with documents and summaries
        serializer = QuerySerializer(q_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

from rest_framework.generics import RetrieveAPIView, ListAPIView

class QueryListView(ListAPIView):
    queryset = Query.objects.all().order_by("-created_at")
    serializer_class = QuerySerializer

class QueryDetailView(RetrieveAPIView):
    queryset = Query.objects.all()
    serializer_class = QuerySerializer
