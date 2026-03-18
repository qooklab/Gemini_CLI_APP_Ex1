import os
import google.generativeai as genai
import traceback
import json
import logging
from firebase_functions import https_fn, options

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 함수가 배포되는 리전을 설정합니다.
options.set_global_options(region="asia-northeast3")

def generate_prompt_for_gemini(original_text, persona):
    """Gemini 모델을 위한 상세하고 효과적인 프롬프트를 생성합니다."""
    persona_map = {
        "boss": "직장 상사",
        "colleague": "타 부서 동료",
        "client": "중요한 외부 고객사 담당자"
    }
    target_audience = persona_map.get(persona, "사람")

    prompt = f"""
    당신은 한국어 비즈니스 커뮤니케이션 전문가입니다.
    다음 '원본 메시지'를 '{target_audience}'에게 보내는 상황이라고 가정하고, 아래 '요구사항'에 맞춰 프로페셔널하고 정중한 한국어 비즈니스 메시지로 변환해주세요.

    [원본 메시지]
    {original_text}

    [요구사항]
    1. 원본 메시지의 핵심 의미는 반드시 유지해야 합니다.
    2. 수신자의 입장을 고려하여 최대한 정중하고 부드러운 어조를 사용해주세요.
    3. 불필요한 미사여구나 서론 없이, 변환된 최종 메시지만 답변으로 제공해주세요.
    """
    return prompt.strip()

@https_fn.on_request(secrets=["GEMINI_API_KEY"])
def business_tone_converter(req: https_fn.Request) -> https_fn.Response:
    """Flask 없이 Firebase Function 직접 호출을 처리합니다."""
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }

    if req.method == "OPTIONS":
        return https_fn.Response(status=204, headers=headers)

    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return https_fn.Response(
                json.dumps({"error": "API Key missing"}),
                status=500, mimetype="application/json", headers=headers
            )
        
        genai.configure(api_key=api_key)
        
        data = req.get_json()
        original_text = data.get('text')
        persona = data.get('persona', 'boss')

        # 모델 리스트 가져오기 (디버깅용)
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as le:
            available_models = [f"Error listing models: {str(le)}"]

        # 시도할 모델 리스트 (최신 안정화 모델 순서)
        model_names = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-3.1-pro']
        
        last_exception = None
        for m_name in model_names:
            try:
                logger.info(f"Attempting with model: {m_name}")
                model = genai.GenerativeModel(m_name)
                prompt = generate_prompt_for_gemini(original_text, persona)
                response = model.generate_content(prompt)
                
                if response.parts:
                    transformed_text = ''.join(part.text for part in response.parts)
                    return https_fn.Response(
                        json.dumps({"transformed_text": transformed_text.strip()}),
                        mimetype="application/json", headers=headers
                    )
            except Exception as e:
                logger.error(f"Failed with {m_name}: {str(e)}")
                last_exception = e
                continue

        # 모든 시도가 실패한 경우
        return https_fn.Response(
            json.dumps({
                "error": f"모든 모델 호출 실패: {str(last_exception)}",
                "available_models": available_models
            }),
            status=500, mimetype="application/json", headers=headers
        )

    except Exception as e:
        return https_fn.Response(
            json.dumps({"error": str(e)}),
            status=500, mimetype="application/json", headers=headers
        )
