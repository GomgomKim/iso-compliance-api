import google.generativeai as genai
from typing import Optional, List
import json

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiService:
    """Service for interacting with Google's Gemini AI."""

    def __init__(self):
        self._model = None
        self._initialized = False

    def _initialize(self):
        """Initialize the Gemini client."""
        if self._initialized:
            return

        if not settings.GCP_PROJECT_ID:
            logger.warning("GCP_PROJECT_ID not set, Gemini service will not be available")
            return

        try:
            genai.configure(api_key=settings.GOOGLE_APPLICATION_CREDENTIALS)
            self._model = genai.GenerativeModel("gemini-1.5-flash")
            self._initialized = True
            logger.info("Gemini AI service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    @property
    def model(self):
        """Get the Gemini model instance."""
        if not self._initialized:
            self._initialize()
        return self._model

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """Generate text using Gemini."""
        if not self.model:
            logger.error("Gemini model not initialized")
            return None

        try:
            generation_config = genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            if system_instruction:
                model = genai.GenerativeModel(
                    "gemini-1.5-flash",
                    system_instruction=system_instruction,
                )
            else:
                model = self.model

            response = model.generate_content(
                prompt,
                generation_config=generation_config,
            )

            return response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return None

    async def analyze_document(
        self,
        document_content: str,
        control_id: str,
        control_name: str,
    ) -> Optional[dict]:
        """Analyze a document for compliance with a specific control."""
        prompt = f"""
다음 문서 내용을 분석하여 ISO 27001:2022 Annex A 컨트롤 '{control_id} - {control_name}'에 대한 준수 여부를 평가해주세요.

문서 내용:
{document_content[:5000]}  # Limit content length

다음 형식의 JSON으로 응답해주세요:
{{
    "compliance_score": 0-100,
    "findings": ["발견 사항 1", "발견 사항 2"],
    "recommendations": ["개선 권고 사항 1", "개선 권고 사항 2"],
    "evidence_found": true/false,
    "summary": "요약 내용"
}}
"""

        try:
            response = await self.generate_text(
                prompt,
                system_instruction="당신은 ISO 27001 보안 전문가입니다. 문서를 분석하고 컴플라이언스 평가를 수행합니다.",
                max_tokens=2048,
                temperature=0.3,
            )

            if response:
                # Try to parse JSON from response
                try:
                    # Find JSON in response
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    if start != -1 and end > start:
                        json_str = response[start:end]
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Gemini response as JSON")

            return None
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            return None

    async def suggest_tasks(
        self,
        control_id: str,
        control_name: str,
        organization_profile: str,
    ) -> Optional[List[dict]]:
        """Suggest tasks for implementing a control based on organization profile."""
        prompt = f"""
'{organization_profile}' 유형의 조직이 ISO 27001:2022 Annex A 컨트롤 '{control_id} - {control_name}'을 구현하기 위해 수행해야 할 구체적인 태스크 목록을 생성해주세요.

다음 형식의 JSON 배열로 응답해주세요:
[
    {{
        "title": "태스크 제목",
        "description": "상세 설명",
        "priority": "high/medium/low",
        "estimated_days": 예상 소요일
    }}
]

최대 5개의 태스크를 제안해주세요.
"""

        try:
            response = await self.generate_text(
                prompt,
                system_instruction="당신은 ISO 27001 구현 컨설턴트입니다. 조직 유형에 맞는 실용적인 태스크를 제안합니다.",
                max_tokens=2048,
                temperature=0.5,
            )

            if response:
                try:
                    start = response.find("[")
                    end = response.rfind("]") + 1
                    if start != -1 and end > start:
                        json_str = response[start:end]
                        return json.loads(json_str)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse Gemini response as JSON array")

            return None
        except Exception as e:
            logger.error(f"Task suggestion failed: {e}")
            return None


# Singleton instance
gemini_service = GeminiService()


def get_gemini_service() -> GeminiService:
    return gemini_service
