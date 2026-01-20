#!/usr/bin/env python3
"""
LMStudio 연결 테스트 및 간단한 분류 테스트
"""

import requests
import json

# LMStudio 설정
ENDPOINT = "http://203.234.62.45:1234/v1/chat/completions"
API_KEY = "lm-studio"
MODEL_NAME = "openai/gpt-oss-20b"

# 간단한 시스템 프롬프트
SIMPLE_PROMPT = "뉴스를 자동차 관련(1) 또는 무관(0)으로 분류하시오. 숫자만 출력하시오."

def test_connection():
    """기본 연결 테스트"""
    try:
        response = requests.post(
            ENDPOINT,
            headers={
                "Content-Type": "application/json", 
                "Authorization": f"Bearer {API_KEY}"
            },
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": "안녕하세요"}],
                "max_tokens": 10,
                "temperature": 0
            },
            timeout=10
        )
        
        print(f"연결 테스트 - 상태 코드: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"응답: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"오류 응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"연결 실패: {str(e)}")
        return False

def test_classification():
    """간단한 분류 테스트"""
    test_cases = [
        "현대차 전기차 판매 증가",
        "네이버 검색 서비스 개선",
        "삼성SDI 배터리 공장 건설"
    ]
    
    for i, title in enumerate(test_cases, 1):
        print(f"\n[테스트 {i}] {title}")
        
        try:
            response = requests.post(
                ENDPOINT,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {API_KEY}"
                },
                json={
                    "model": MODEL_NAME, 
                    "messages": [
                        {"role": "system", "content": SIMPLE_PROMPT},
                        {"role": "user", "content": f"제목: {title}"}
                    ],
                    "max_tokens": 3,
                    "temperature": 0
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                output = result['choices'][0]['message']['content'].strip()
                print(f"응답: '{output}'")
            else:
                print(f"실패: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"오류: {str(e)}")

if __name__ == "__main__":
    print("🔍 LMStudio 연결 테스트")
    print("=" * 40)
    
    if test_connection():
        print("\n✅ 연결 성공! 분류 테스트 진행...")
        test_classification()
    else:
        print("\n❌ 연결 실패!")
        print("\n확인 사항:")
        print("1. LMStudio가 실행 중인가요?")
        print("2. 로컬 서버가 시작되었나요? (포트 1234)")
        print("3. 모델이 로드되었나요?")
        print("4. Server 탭에서 'Start Server' 버튼을 눌렀나요?")