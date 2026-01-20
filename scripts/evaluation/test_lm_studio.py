"""
LM Studio 연결 테스트
"""

import requests
import json

def test_lm_studio():
    """LM Studio 연결 테스트"""
    print("LM Studio 연결 테스트 시작...")

    # 1. 서버 상태 확인
    try:
        response = requests.get("http://localhost:1234/v1/models", timeout=5)
        print(f"O 서버 연결 성공!")
        print(f"  사용 가능한 모델: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("X LM Studio 서버에 연결할 수 없습니다!")
        print("  1. LM Studio를 실행하세요")
        print("  2. 서버를 시작하세요 (Start Server)")
        print("  3. 모델을 로드하세요")
        return False
    except Exception as e:
        print(f"X 오류: {e}")
        return False

    # 2. 간단한 테스트 쿼리
    print("\n간단한 테스트 쿼리 실행...")

    headers = {"Content-Type": "application/json"}
    payload = {
        "messages": [
            {"role": "system", "content": "답변: 1 또는 0만"},
            {"role": "user", "content": "테스트"}
        ],
        "temperature": 0.1,
        "max_tokens": 10
    }

    try:
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']
            print(f"O 응답 성공: {answer}")
            return True
        else:
            print(f"X 응답 실패: {response.status_code}")
            print(f"  에러: {response.text}")
            return False

    except Exception as e:
        print(f"X 쿼리 실패: {e}")
        return False

if __name__ == "__main__":
    test_lm_studio()