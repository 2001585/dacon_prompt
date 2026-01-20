"""
초고속 테스트 - 10개 샘플만
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
            {"role": "user", "content": f"[Article]\n{user_input}"}
        ],
        "temperature": 0.1,
        "max_tokens": 10,
        "stream": False
    }

    try:
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except:
        return "0"

# 가장 유망한 영어 프롬프트
prompt = """Output "1" or "0" only.

IMMEDIATE 0:
- ESS, UAM, aviation, railway
- Policy/trade only
- No car company mentioned

IMMEDIATE 1:
- Hyundai, Kia, Tesla, BMW
- "vehicle" or "automotive" stated

Default: 0"""

def main():
    df = pd.read_csv('data/samples.csv')

    # 10개만 (5개씩)
    df_test = pd.concat([
        df[df['label'] == 1].head(5),
        df[df['label'] == 0].head(5)
    ])

    print(f"초고속 테스트: 10개 샘플")
    print(f"프롬프트 길이: {len(prompt)}자")
    print("=" * 50)

    correct = 0

    for idx, row in df_test.iterrows():
        user_input = f"Title: {row['title']}\nContent: {row['content']}"
        response = call_lm_studio(prompt, user_input)

        predicted = 1 if "1" in response[:10] else 0
        actual = row['label']

        is_correct = predicted == actual
        if is_correct:
            correct += 1

        status = "O" if is_correct else f"X(예측={predicted},정답={actual})"
        print(f"{idx:2}: {status} - {row['title'][:40]}...")

    accuracy = correct / len(df_test)
    print(f"\n정확도: {accuracy:.0%} ({correct}/10)")

    if accuracy >= 0.7:
        print("\n[유망] 이 프롬프트는 가능성이 있음!")
    else:
        print("\n[실패] 다른 접근 필요")

if __name__ == "__main__":
    main()