import os
import google.generativeai as genai
import traceback
from flask import Flask, request, jsonify
from firebase_functions import https_fn, options

# --- Debug: Print all environment variables ---
print("----- All Environment Variables -----")
print(os.environ)
print("---------------------------------")
# --- End Debug ---

# 함수가 배포되는 리전을 설정합니다.
options.set_global_options(region="asia-northeast3")

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Gemini API 설정 ---
# API 키를 환경 변수에서 직접 가져옵니다.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("환경 변수에서 Gemini API 키를 성공적으로 설정했습니다.")
else:
    print("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. API를 사용할 수 없습니다.")
# --- 설정 종료 ---

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

@app.route('/convert', methods=['POST'])
def convert():
    """Gemini API를 사용하여 텍스트 변환 요청을 처리합니다."""
    if not GEMINI_API_KEY:
        return jsonify({"error": "서버에 Gemini API 키가 설정되지 않았습니다. 관리자에게 문의하세요."}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "잘못된 JSON 형식입니다."}), 400

        original_text = data.get('text')
        persona = data.get('persona', 'boss')

        if not original_text or not original_text.strip():
            return jsonify({"error": "변환할 텍스트 내용이 필요합니다."}), 400

        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = generate_prompt_for_gemini(original_text, persona)

        response = model.generate_content(prompt)

        # 안전 장치 등으로 인해 응답에 텍스트가 없는 경우 처리
        if response.parts:
            transformed_text = ''.join(part.text for part in response.parts)
        else:
            transformed_text = "[AI 모델이 답변 생성을 거부했습니다. 입력 내용을 확인해주세요.]"
            print(f"응답에 문제가 있습니다: {response.prompt_feedback}")

        return jsonify({"transformed_text": transformed_text})

    except Exception as e:
        print(f"Gemini API 호출 중 오류 발생: {e}")
        print(traceback.format_exc()) # Add this line for traceback
        return jsonify({"error": "AI 모델과 통신 중 내부 오류가 발생했습니다."}), 500



@https_fn.on_request()
def business_tone_converter(req: https_fn.Request) -> https_fn.Response:
    """Flask 앱을 위한 Firebase Function 래퍼입니다."""
    with app.request_context(req.environ):
        return app.full_dispatch_request()
