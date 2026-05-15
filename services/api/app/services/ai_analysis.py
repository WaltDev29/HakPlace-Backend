import json
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI

class AIAnalysisService:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY")
        if not self.api_key:
            # Fallback for LLM_API_KEY if not found directly
            self.api_key = os.getenv("OPENAI_API_KEY")
            
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "gpt-4o-mini"

    def analyze_weekly_reviews(self, context: Dict[str, Any], previous_analysis: Optional[str] = None) -> Dict[str, Any]:
        """
        주간 리뷰 분석 수행
        context: {
            "analysis_date": "...",
            "period_value": "...",
            "meals": [
                {
                    "date": "...",
                    "day": "...",
                    "type": "...",
                    "avg_rating": 4.5,
                    "foods": [...],
                    "reviews": ["...", "..."]
                },
                ...
            ]
        }
        """
        if not self.client:
            return {"error": "LLM_API_KEY not configured"}

        system_prompt = """
당신은 학교 급식 데이터를 분석하는 전문 AI 분석가입니다. 
제공된 주간 식단 데이터와 학생들의 리뷰를 바탕으로 이번 주의 급식 만족도를 분석하고 구조화된 JSON 응답을 생성해야 합니다.

응답은 반드시 다음 JSON 형식을 따라야 합니다:
    {
      "analysis_date": "오늘 날짜",
      "period_value": "분석 대상 주 (월요일 날짜)",
      "meals_summary": [
        {
          "date": "날짜",
          "day": "요일",
          "type": "식사 종류(조식/중식/석식)",
          "avg_rating": 현재 평균 평점 (평점 0은 데이터 미집계이므로 무시할 것),
          "prev_rating": 이전 분석 시점의 평균 평점 (평점 0은 데이터 미집계이므로 무시할 것),
          "foods": ["음식1", "음식2", ...]
        }
      ],
      "ai_analysis": "이번 주 전반적인 평가 및 특징 요약 (3-4문장)",
      "trend_analysis": "이전 분석 결과 대비 변화 추이 분석 (평점 0은 데이터 미집계이므로 무시할 것)",
      "key_feedback": "한 달간 반복된 주요 피드백 내용"
    }
"""
        
        user_prompt = f"""
오늘 날짜: {context['analysis_date']}
분석 대상 주 (월요일 기준): {context['period_value']}

[이번 주 식단 및 리뷰 데이터]
{json.dumps(context['meals'], ensure_ascii=False, indent=2)}

[이전 분석 결과 및 당시 평점 데이터]
{previous_analysis if previous_analysis else "이전 분석 데이터가 없습니다. (첫 분석)"}

평점이 0인 경우 평가되지 않았음을 의미하며, 만족도가 낮음을 의미하는 것이 아닙니다.

위 데이터를 바탕으로 이번 주의 만족도 변화와 특징을 분석해줘.
특히 이전 분석 데이터가 있다면, 당시의 식단별 평점과 현재 평점을 비교하여 평가가 어떻게 변했는지(상승/하락)와 특정 메뉴에 대한 반응 변화를 'trend_analysis'에 간단하게 작성해줘.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": f"AI 분석 중 오류 발생: {str(e)}"}

    def analyze_monthly_reviews(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        월간 리뷰 분석 수행
        context: {
            "analysis_date": "...",
            "period_value": "...",
            "weekly_summaries": [
                { "period_value": "...", "ai_analysis": "...", "avg_rating": ... },
                ...
            ]
        }
        """
        if not self.client:
            return {"error": "LLM_API_KEY not configured"}

        system_prompt = """
당신은 학교 급식 데이터를 분석하는 전문 AI 분석가입니다. 
한 달 동안의 주간 분석 결과들을 종합하여 월간 통계 리포트를 작성하고 구조화된 JSON 응답을 생성해야 합니다.

응답 형식:
{
  "analysis_date": "오늘 날짜",
  "period_value": "분석 대상 월 (YYYY-MM)",
  "ai_analysis": "이번 달 전반적인 평가 및 특징 요약 (3-4문장)",
  "trend_analysis": "주차별 평점 변화 요약 (평점 0은 데이터 미집계이므로 무시할 것)",
  "key_feedback": "한 달간 반복된 주요 피드백 내용"
}
"""
        
        user_prompt = f"""
오늘 날짜: {context['analysis_date']}
분석 대상 월: {context['period_value']}

[주간 분석 데이터 목록]
{json.dumps(context['weekly_summaries'], ensure_ascii=False, indent=2)}

평점이 0인 경우 평가되지 않았음을 의미하며, 만족도가 낮음을 의미하는 것이 아닙니다.

위 데이터를 종합하여 한 달간의 급식 만족도 흐름을 분석해줘.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"error": f"AI 분석 중 오류 발생: {str(e)}"}

ai_service = AIAnalysisService()
