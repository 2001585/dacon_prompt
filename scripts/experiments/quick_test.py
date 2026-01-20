"""
빠른 테스트 - 샘플 5개만 평가
"""

import pandas as pd
import requests
import json
import time

def call_lm_studio(prompt: str, user_input: str) -> str:
    """LM Studio API 호출"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"[기사]\n{user_input}"}
        ],
        "temperature": 0.1,
        "max_tokens": 10,
        "stream": False
    }

    try:
        print("    API 호출 중...", end='')
        start = time.time()
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60  # 60초 타임아웃
        )
        elapsed = time.time() - start
        print(f" {elapsed:.1f}초")

        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"\n    에러: {e}")
        return "0"

# 간단한 프롬프트
prompt = """[역할] 자동차 뉴스 분류
[출력] "1" 또는 "0"만

자동차 관련이면 1, 아니면 0"""

# 샘플 데이터 로드
df = pd.read_csv('data/samples.csv')
print(f"샘플 데이터: {len(df)}개 중 5개만 테스트\n")

# 처음 5개만 테스트
correct = 0
for idx, row in df.head(5).iterrows():
    print(f"\nSample {idx+1}:")
    print(f"  제목: {row['title'][:50]}...")

    user_input = f"제목: {row['title']}\n본문: {row['content']}"
    response = call_lm_studio(prompt, user_input)

    predicted = 1 if "1" in response[:10] else 0
    actual = row['label']

    is_correct = predicted == actual
    status = "O" if is_correct else "X"

    print(f"  [{status}] 실제={actual}, 예측={predicted}, 응답='{response}'")

    if is_correct:
        correct += 1

print(f"\n정확도: {correct}/5 = {correct/5:.0%}")