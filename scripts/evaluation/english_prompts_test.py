"""
Llama-3.2에 최적화된 영어 프롬프트 테스트
단순하고 명확한 규칙 사용
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
    except Exception as e:
        return "0"

# 영어 기반 단순 프롬프트들
prompts = {
    "EN_Simple_300": """Classify: Automotive news = 1, Others = 0

NOT automotive (return 0):
- ESS, UAM, aviation, railway, shipbuilding
- Policy, trade, economy only
- Consumer electronics

IS automotive (return 1):
- Hyundai, Kia, Tesla, BMW, Mercedes, Toyota
- "vehicle", "automotive", "car" explicitly mentioned
- EV battery/chip WITH "vehicle" stated

Default: 0
Output: only "1" or "0" """,

    "EN_Negative_First_350": """Output "1" or "0" only.

IMMEDIATE 0:
- Energy Storage System (ESS)
- Urban Air Mobility (UAM)
- Aviation, railway, marine
- Semiconductor/battery WITHOUT "vehicle"
- Policy/trade only

IMMEDIATE 1:
- Car makers: Hyundai, Kia, Tesla, GM, Ford
- Contains "vehicle", "automotive", "car"
- Auto parts WITH car context

Unclear = 0""",

    "EN_Korean_Mix_400": """[Auto News Filter] "1" or "0"

Block (→0):
ESS/UAM/항공/철도/조선/정책only

Pass (→1):
현대차/기아/Tesla/BMW/Mercedes
"vehicle"/"automotive" stated
전장부품 with 자동차 context

Rule:
- Check block list first
- Need explicit auto signal
- Default = 0

Output: "1" or "0" only""",

    "EN_Decision_Tree_450": """Automotive classifier. Output "1" or "0".

Step 1: Check exclusions
If ESS/UAM/aviation/railway → return 0
If policy/trade only → return 0

Step 2: Check inclusions
If Hyundai/Kia/Tesla mentioned → return 1
If "vehicle"/"automotive" explicit → return 1

Step 3: Context check
If battery+vehicle → 1
If battery alone → 0
If parts+car company → 1
If parts alone → 0

Default: 0"""
}

def test_prompts():
    """프롬프트 테스트"""
    df = pd.read_csv('data/samples.csv')

    # 균형잡힌 20개 샘플
    df_test = pd.concat([
        df[df['label'] == 1].head(10),
        df[df['label'] == 0].head(10)
    ]).reset_index(drop=True)

    print(f"테스트 샘플: {len(df_test)}개")
    print("=" * 60)

    results = []

    for name, prompt in prompts.items():
        print(f"\n[{name}]")
        print(f"길이: {len(prompt)}자")

        correct = 0
        predictions = []

        for idx, row in df_test.iterrows():
            # 영어로 테스트하되 제목/본문은 그대로
            user_input = f"Title: {row['title']}\nContent: {row['content']}"
            response = call_lm_studio(prompt, user_input)

            predicted = 1 if "1" in response[:10] else 0
            actual = row['label']
            is_correct = predicted == actual

            if is_correct:
                correct += 1

            predictions.append({
                'id': row.get('ID', row.get('id', idx)),
                'predicted': predicted,
                'actual': actual,
                'correct': is_correct
            })

            # 진행 표시
            status = "O" if is_correct else "X"
            print(f"  {idx+1:2}: {status}", end="")
            if (idx + 1) % 10 == 0:
                print()

        accuracy = correct / len(df_test)

        results.append({
            'name': name,
            'accuracy': accuracy,
            'correct': correct,
            'total': len(df_test),
            'length': len(prompt),
            'predictions': predictions
        })

        print(f"\n정확도: {accuracy:.1%} ({correct}/{len(df_test)})")

    return results

def analyze_best(results):
    """최고 성능 프롬프트 분석"""
    print("\n" + "=" * 60)
    print("[결과 분석]")
    print("=" * 60)

    # 정확도 순 정렬
    sorted_results = sorted(results, key=lambda x: x['accuracy'], reverse=True)

    print("\n[정확도 순위]")
    for i, r in enumerate(sorted_results, 1):
        accuracy = r['accuracy']
        length = r['length']

        # Dacon 점수 계산
        if length <= 300:
            length_score = 1.0
        else:
            length_score = math.sqrt(1 - ((length - 300) / 2700) ** 2)
        dacon_score = 0.9 * accuracy + 0.1 * length_score

        print(f"{i}. {r['name']}")
        print(f"   정확도: {accuracy:.1%}")
        print(f"   예상 Dacon: {dacon_score:.4f}")
        print(f"   길이: {length}자")

    # 최고 성능 프롬프트
    best = sorted_results[0]

    # 오류 분석
    false_positives = 0
    false_negatives = 0
    for p in best['predictions']:
        if not p['correct']:
            if p['actual'] == 0 and p['predicted'] == 1:
                false_positives += 1
            elif p['actual'] == 1 and p['predicted'] == 0:
                false_negatives += 1

    print(f"\n[최고 성능: {best['name']}]")
    print(f"  오류 유형: FP={false_positives}, FN={false_negatives}")

    # 전체 데이터셋 예상
    print(f"\n[전체 46개 샘플 예상 성능]")
    print(f"  예상 정확도: {best['accuracy']:.1%}")

    if best['accuracy'] > 0.7:
        print("\n[성공] Llama-3.2에서 70% 이상 달성!")
        print("이 프롬프트를 전체 샘플로 테스트 권장")
    else:
        print("\n[주의] 아직 성능이 부족함")
        print("더 단순한 규칙이나 다른 접근 필요")

    return best

def save_best_prompt(best, prompts):
    """최고 프롬프트 저장"""
    with open('prompts/generated/best_english_prompt.txt', 'w', encoding='utf-8') as f:
        f.write(f"[Best English Prompt for Llama-3.2]\n")
        f.write(f"Name: {best['name']}\n")
        f.write(f"Test Accuracy: {best['accuracy']:.1%}\n")
        f.write(f"Length: {best['length']} chars\n")
        f.write(f"\n[Prompt Content]\n")
        f.write(prompts[best['name']])
        f.write(f"\n\n[Note]\n")
        f.write(f"This prompt is optimized for Llama-3.2\n")
        f.write(f"Uses negative-first approach to avoid over-generalization\n")

    print(f"\n최고 프롬프트 저장: prompts/generated/best_english_prompt.txt")

if __name__ == "__main__":
    print("영어 기반 Llama-3.2 최적화 프롬프트 테스트")
    print("=" * 60)

    # 테스트 실행
    results = test_prompts()

    # 분석
    best = analyze_best(results)

    # 저장
    save_best_prompt(best, prompts)
