"""
게이트 조건 핵심 프롬프트 3개만 빠르게 테스트
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
        print(f"    에러: {e}")
        return "0"

def calculate_dacon_score(accuracy: float, prompt_length: int) -> float:
    """Dacon 점수 계산"""
    if prompt_length <= 300:
        length_score = 1.0
    else:
        length_score = math.sqrt(1 - ((prompt_length - 300) / 2700) ** 2)
    return 0.9 * accuracy + 0.1 * length_score

# 핵심 3개 프롬프트만
prompts = {
    "V3_게이트조건_480자": """[자동차뉴스분류] "1" 또는 "0"만

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

    "V4_단순화_400자": """[자동차분류]

핵심: 현대차/기아/테슬라/BMW/벤츠/폭스바겐
부품: 전장/배터리/타이어/충전/자율주행
행위: 생산/출시/판매/투자/수주/계약

판정:
1) 핵심기업 → 1
2) 차량용 명시 → 1
3) 부품+행위 동시 → 1
4) ESS/UAM/항공 → 0
5) 애매 → 0

출력: "1" 또는 "0"만""",

    "V10_핵심키워드_380자": """[자동차뉴스]

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
    print(f"샘플 수: {len(df)}개")
    print("=" * 80)

    results = []

    for name, prompt in prompts.items():
        print(f"\n[{name}]")
        print(f"길이: {len(prompt)}자")

        correct = 0
        detailed = []

        start_time = time.time()

        for idx, row in df.iterrows():
            user_input = f"제목: {row['title']}\n본문: {row['content']}"
            response = call_lm_studio(prompt, user_input)

            predicted = 1 if "1" in response[:10] else 0
            actual = row['label']
            is_correct = predicted == actual

            if is_correct:
                correct += 1

            detailed.append({
                'id': row.get('ID', row.get('id', idx)),
                'title': row['title'][:50],
                'predicted': predicted,
                'actual': actual,
                'correct': is_correct
            })

            # 진행 표시
            if (idx + 1) % 10 == 0:
                elapsed = time.time() - start_time
                print(f"  {idx+1}/{len(df)} ({elapsed:.1f}초)")

        accuracy = correct / len(df)
        dacon_score = calculate_dacon_score(accuracy, len(prompt))

        results.append({
            'name': name,
            'accuracy': accuracy,
            'dacon_score': dacon_score,
            'correct': correct,
            'total': len(df),
            'length': len(prompt),
            'detailed': detailed
        })

        print(f"정확도: {accuracy:.1%} ({correct}/{len(df)})")
        print(f"Dacon 점수: {dacon_score:.4f}")

    # 결과 분석
    print("\n" + "=" * 80)
    print("[결과 요약]")
    print("=" * 80)

    # 최고 성능 찾기
    best = max(results, key=lambda x: x['accuracy'])
    print(f"\n최고 정확도: {best['name']}")
    print(f"  정확도: {best['accuracy']:.1%}")
    print(f"  Dacon 점수: {best['dacon_score']:.4f}")

    # 샘플별 분석
    sample_correct_count = {}
    for r in results:
        for d in r['detailed']:
            sid = d['id']
            if sid not in sample_correct_count:
                sample_correct_count[sid] = {
                    'title': d['title'],
                    'actual': d['actual'],
                    'correct': 0
                }
            if d['correct']:
                sample_correct_count[sid]['correct'] += 1

    # 모두 맞춘 샘플
    all_correct = [k for k, v in sample_correct_count.items() if v['correct'] == len(results)]
    print(f"\n모든 프롬프트가 맞춘 샘플: {len(all_correct)}개")

    # 모두 틀린 샘플
    all_wrong = [k for k, v in sample_correct_count.items() if v['correct'] == 0]
    print(f"모든 프롬프트가 틀린 샘플: {len(all_wrong)}개")

    if all_wrong:
        print("\n[문제 샘플 (모두 실패)]")
        for sid in all_wrong[:5]:
            data = sample_correct_count[sid]
            print(f"  Sample {sid}: {data['title']}... (정답={data['actual']})")

    # 결과 저장
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    with open(f'results/gate_test_results_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: results/gate_test_results_{timestamp}.json")

if __name__ == "__main__":
    print("게이트 조건 기반 프롬프트 빠른 테스트")
    print("=" * 80)
    main()
