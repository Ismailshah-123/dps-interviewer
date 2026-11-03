from .base import SummarizationProvider
from app.schemas.ai import StructuredSummary
class DeterministicSummarizationProvider(SummarizationProvider):
    name='deterministic-test'; model_name='synthetic-fixture'; prompt_version='test-v1'
    async def summarize(self, transcript, segments):
        return StructuredSummary(interview_overview='Synthetic interview fixture for automated testing.', parent_guardian_statements=['Family expects a supportive school environment.'], student_statements=['Student enjoys football and science.'], educational_background=['Mathematics and reading were discussed.'], interests_and_activities=['Football','Science'], school_expectations=['Supportive school environment.'], important_topics=['Student interests'], follow_up_questions=[], unclear_or_missing_information=[])
