"""
게이트 조건 프롬프트 - 샘플 20개만 빠른 테스트
"""

import pandas as pd
import requests
import json
import time
import math

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
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        return "0"

# 가장 유망한 2개 프롬프트
prompts = {
    "게이트조건_480자": """[자동차뉴스분류] "1" 또는 "0"만

[집합정의]
A=완성차·OEM·전장·부품·타이어·충전·차량용배터리
Act=출시·양산·생산·투자·수주·공급계약·판매
B=정책·무역·ESS·UAM·항공·철도·조선

[점수계산]
+3 주체가A
+2 행위가Act
+1 차량용명시
+1 A와Act동시출현
-3 B중심
-2 차량용불명확

[판정규칙]
합계≥3 그리고 (차량용명시 또는 A와Act동시)→1
그외→0
모호→0""",

    "단순판정_380자": """[자동차뉴스]

자동차신호:
현대차/기아/테슬라/BMW/벤츠
전기차/수소차/자율주행
차량용/자동차용/오토모티브
전장부품/차량반도체/차량배터리

비자동차신호:
ESS/UAM/항공/철도/조선
가전/스마트폰/TV/모니터

판정:
자동차신호 2개이상 → 1
비자동차신호 있음 → 0
자동차신호 1개 → 문맥확인
문맥애매 → 0

출력: "1" 또는 "0"만"""
}

def main():
    df = pd.read_csv('data/samples.csv')

    # 20개만 테스트 (균형있게 선택)
    df_test = pd.concat([
        df[df['label'] == 1].head(10),  # 자동차 10개
        df[df['label'] == 0].head(10)   # 비자동차 10개
    ]).reset_index(drop=True)

    print(f"테스트 샘플: {len(df_test)}개 (자동차 10, 비자동차 10)")
    print("=" * 60)

    results = []

    for name, prompt in prompts.items():
        print(f"\n[{name}]")
        print(f"길이: {len(prompt)}자")

        correct = 0
        errors = []

        for idx, row in df_test.iterrows():
            print(f"  샘플 {idx+1}/{len(df_test)}...", end='')

            user_input = f"제목: {row['title']}\n본문: {row['content']}"
            response = call_lm_studio(prompt, user_input)

            predicted = 1 if "1" in response[:10] else 0
            actual = row['label']
            is_correct = predicted == actual

            if is_correct:
                correct += 1
                print(" O")
            else:
                print(f" X (예측={predicted}, 정답={actual})")
                errors.append({
                    'id': row.get('ID', row.get('id', idx)),
                    'title': row['title'][:50],
                    'predicted': predicted,
                    'actual': actual
                })

        accuracy = correct / len(df_test)

        results.append({
            'name': name,
            'accuracy': accuracy,
            'correct': correct,
            'total': len(df_test),
            'errors': errors
        })

        print(f"\n정확도: {accuracy:.1%} ({correct}/{len(df_test)})")

        if errors:
            print("틀린 샘플:")
            for e in errors[:3]:  # 처음 3개만
                print(f"  - {e['title']}...")

    # 전체 데이터셋 예상 점수
    print("\n" + "=" * 60)
    print("[전체 데이터셋 예상 성능]")
    print("=" * 60)

    for r in results:
        # 20개 샘플 기준으로 전체 46개 예상
        estimated_accuracy = r['accuracy']
        prompt_length = len(prompts[r['name']])

        if prompt_length <= 300:
            length_score = 1.0
        else:
            length_score = math.sqrt(1 - ((prompt_length - 300) / 2700) ** 2)

        dacon_score = 0.9 * estimated_accuracy + 0.1 * length_score

        print(f"\n{r['name']}:")
        print(f"  테스트 정확도: {r['accuracy']:.1%}")
        print(f"  예상 Dacon 점수: {dacon_score:.4f}")
        print(f"  프롬프트 길이: {prompt_length}자")

    # 최종 추천
    best = max(results, key=lambda x: x['accuracy'])
    print("\n" + "=" * 60)
    print(f"추천 프롬프트: {best['name']}")
    print(f"테스트 정확도: {best['accuracy']:.1%}")
    print("=" * 60)

if __name__ == "__main__":
    print("게이트 조건 프롬프트 미니 테스트")
    print("=" * 60)
    main()