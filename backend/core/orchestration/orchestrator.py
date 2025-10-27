from ..agents.research_gathering import ResearchGatheringAgent
from ..agents.summarization import SummarizationAgent
from ..agents.knowledge_manager import KnowledgeManagerAgent

class Orchestrator:
    def __init__(self):
        self.gather_agent = ResearchGatheringAgent()
        self.summary_agent = SummarizationAgent()
        self.knowledge_agent = KnowledgeManagerAgent()

    def process_query(self, query_text: str, summary_type="medium"):
        """Main pipeline for handling a research query."""
        # Check if query exists
        existing_query = self.knowledge_agent.get_existing_query(query_text)
        if existing_query:
            cached_summary = self.knowledge_agent.get_summary(existing_query, summary_type)
            if cached_summary:
                return {
                    "query": query_text,
                    "summary": cached_summary.summary_text,
                    "cached": True,
                }

        # Step 1: Gather
        query_obj = self.gather_agent.gather(query_text)
        if not query_obj:
            return {"error": "Failed to gather research data."}

        # Step 2: Summarize
        summary_obj = self.summary_agent.summarize(query_obj, summary_type)
        if not summary_obj:
            return {"error": "Failed to summarize data."}

        return {
            "query": query_text,
            "summary": summary_obj.summary_text,
            "cached": False,
        }
