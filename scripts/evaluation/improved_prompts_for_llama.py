"""
게이트 조건 기반 개선된 프롬프트들을 Llama-3.2로 테스트
김경태 프롬프트의 핵심 성공 요인을 반영한 버전들
"""

import pandas as pd
import requests
import json
import time
from datetime import datetime
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
            timeout=60
        )
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"    API 에러: {e}")
        return "0"

def calculate_dacon_score(accuracy: float, prompt_length: int) -> float:
    """실제 Dacon 점수 계산"""
    if prompt_length <= 300:
        length_score = 1.0
    else:
        length_score = math.sqrt(1 - ((prompt_length - 300) / 2700) ** 2)
    return 0.9 * accuracy + 0.1 * length_score

# 게이트 조건 기반 개선된 프롬프트들
prompts = {
    "V3_게이트조건_500자": """[자동차뉴스분류] "1" 또는 "0"만

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

    "V4_단순화게이트_450자": """[자동차분류]

핵심주체: 현대차/기아/테슬라/폭스바겐/도요타/BMW/벤츠/폴스타
자동차부품: 전장/배터리/타이어/충전인프라/자율주행
자동차행위: 생산/출시/판매/투자/수주/공급계약

판정:
1) 핵심주체 언급 → 1
2) 차량용/자동차용 명시 → 1
3) 자동차부품+자동차행위 동시 → 1
4) ESS/UAM/항공/철도 → 0
5) 애매하면 → 0

출력: "1" 또는 "0"만""",

    "V5_영어혼합_480자": """[Automotive News Classification]
Output: "1" or "0" only

[Core]
Automotive: OEM/Parts/Battery/Tire/Charging/ADAS
Action: Launch/Production/Sales/Investment/Contract
Non-Auto: ESS/UAM/Aviation/Railway/Policy

[Rules]
1. OEM mentioned → 1
2. "vehicle-specific" stated → 1
3. Automotive+Action together → 1
4. Non-Auto focus → 0
5. Unclear → 0

차량용/자동차용 명시되면 1
애매하면 0""",

    "V6_우선순위명확_470자": """[자동차뉴스판정]

최우선(즉시1):
- 현대차/기아/테슬라 언급
- 차량용/자동차용/오토모티브 명시

중요신호(점수합산):
+2 전장부품/배터리/타이어
+2 생산/출시/수주/공급
+1 자율주행/전기차/수소차

차단신호(즉시0):
- ESS/UAM/항공기/철도
- 정책/규제만 언급
- 반도체/배터리인데 차량용 불명

최종: 점수≥3이면 1, 아니면 0
모호하면 0""",

    "V7_김경태간소화_520자": """[자동차뉴스] "1" 또는 "0"

A집합: 완성차/OEM/현대차/기아/테슬라/BMW/벤츠/폭스바겐
B집합: 전장/부품/타이어/배터리/충전/자율주행
행위: 출시/양산/생산/투자/수주/계약/판매

점수:
+3 A집합 주체
+2 B집합이고 차량용명시
+2 행위 포함
-3 ESS/UAM/항공/철도
-2 배터리/반도체인데 차량용불명

판정:
점수≥3이고 (A집합 또는 차량용명시) → 1
나머지 → 0""",

    "V8_조건트리_490자": """[자동차판별]

1단계: 제목확인
- 완성차기업 → 1로 확정
- ESS/UAM/항공 → 0으로 확정
- 애매 → 2단계

2단계: 본문확인
- 차량용/자동차용 명시 → 1
- 전장+생산/출시 동시 → 1
- 배터리+차량용명시 → 1
- 배터리+차량용불명 → 0

3단계: 문맥확인
- 자동차기업이 주체 → 1
- 자동차행위 수행 → 1
- 나머지 → 0

출력: "1" 또는 "0"만""",

    "V9_부정우선_460자": """[차량뉴스분류]

즉시제외(→0):
UAM/도심항공/항공기/철도/선박/ESS/전력망/가전/스마트폰

즉시포함(→1):
현대차/기아/테슬라/GM/포드/폭스바겐/도요타
차량용/자동차용/vehicle/automotive 명시

추가판정:
+배터리: 차량용명시→1, 불명→0
+반도체: 차량용명시→1, 불명→0
+부품: 자동차언급→1, 불명→0
+충전: 전기차언급→1, 불명→0

애매→0
출력: "1" 또는 "0"만""",

    "V10_핵심키워드_400자": """[자동차뉴스]

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

def evaluate_prompts():
    """모든 프롬프트 평가"""
    df = pd.read_csv('data/samples.csv')
    results = []

    print("[개선된 프롬프트 평가 시작]")
    print(f"샘플 수: {len(df)}개")
    print("=" * 80)

    for name, prompt in prompts.items():
        print(f"\n평가 중: {name}")
        print(f"프롬프트 길이: {len(prompt)}자")

        correct = 0
        predictions = []

        for idx, row in df.iterrows():
            user_input = f"제목: {row['title']}\n본문: {row['content']}"

            # API 호출
            response = call_lm_studio(prompt, user_input)

            # 예측값 추출
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

            # 진행상황 표시
            if (idx + 1) % 10 == 0:
                print(f"  진행: {idx+1}/{len(df)}")

        accuracy = correct / len(df)
        dacon_score = calculate_dacon_score(accuracy, len(prompt))

        result = {
            'name': name,
            'prompt_length': len(prompt),
            'correct': correct,
            'total': len(df),
            'accuracy': accuracy,
            'dacon_score': dacon_score,
            'predictions': predictions
        }

        results.append(result)

        print(f"  정확도: {accuracy:.1%} ({correct}/{len(df)})")
        print(f"  예상 Dacon 점수: {dacon_score:.4f}")

    return results

def analyze_results(results):
    """결과 분석 및 최적 프롬프트 선별"""
    print("\n" + "=" * 80)
    print("[최종 결과 분석]")
    print("=" * 80)

    # 정확도 순 정렬
    sorted_by_accuracy = sorted(results, key=lambda x: x['accuracy'], reverse=True)

    print("\n[정확도 TOP 3]")
    for i, r in enumerate(sorted_by_accuracy[:3], 1):
        print(f"{i}. {r['name']}")
        print(f"   정확도: {r['accuracy']:.1%}")
        print(f"   Dacon 점수: {r['dacon_score']:.4f}")
        print(f"   길이: {r['prompt_length']}자")

    # Dacon 점수 순 정렬
    sorted_by_dacon = sorted(results, key=lambda x: x['dacon_score'], reverse=True)

    print("\n[Dacon 점수 TOP 3]")
    for i, r in enumerate(sorted_by_dacon[:3], 1):
        print(f"{i}. {r['name']}")
        print(f"   Dacon 점수: {r['dacon_score']:.4f}")
        print(f"   정확도: {r['accuracy']:.1%}")
        print(f"   길이: {r['prompt_length']}자")

    # 샘플별 성공률 분석
    sample_success = {}
    for r in results:
        for pred in r['predictions']:
            sid = pred['id']
            if sid not in sample_success:
                sample_success[sid] = {'correct': 0, 'total': 0, 'actual': pred['actual']}
            sample_success[sid]['total'] += 1
            if pred['correct']:
                sample_success[sid]['correct'] += 1

    # 모든 프롬프트가 맞춘 샘플
    all_correct = [sid for sid, data in sample_success.items()
                   if data['correct'] == data['total']]

    # 모든 프롬프트가 틀린 샘플
    all_wrong = [sid for sid, data in sample_success.items()
                 if data['correct'] == 0]

    print(f"\n[샘플 분석]")
    print(f"모든 프롬프트가 맞춘 샘플: {len(all_correct)}개")
    print(f"모든 프롬프트가 틀린 샘플: {len(all_wrong)}개")

    if all_wrong:
        print("\n[주의: 모든 프롬프트가 실패한 샘플]")
        df = pd.read_csv('data/samples.csv')
        for sid in all_wrong[:3]:  # 처음 3개만
            sample = df[df.get('ID', df.get('id')) == sid].iloc[0]
            print(f"  Sample {sid}: {sample['title'][:50]}...")
            print(f"    정답: {sample_success[sid]['actual']}")

    return sorted_by_dacon[0]  # 최고 점수 프롬프트 반환

def save_results(results):
    """결과 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results/improved_prompts_results_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {filename}")

    # 최고 성능 프롬프트 별도 저장
    best = max(results, key=lambda x: x['dacon_score'])

    with open('prompts/generated/best_prompt_for_llama.txt', 'w', encoding='utf-8') as f:
        f.write(f"[최고 성능 프롬프트]\n")
        f.write(f"이름: {best['name']}\n")
        f.write(f"Dacon 점수: {best['dacon_score']:.4f}\n")
        f.write(f"정확도: {best['accuracy']:.1%}\n")
        f.write(f"길이: {best['prompt_length']}자\n")
        f.write(f"\n[프롬프트 내용]\n")
        f.write(prompts[best['name']])

    print(f"최고 성능 프롬프트 저장: prompts/generated/best_prompt_for_llama.txt")

if __name__ == "__main__":
    print("=" * 80)
    print("게이트 조건 기반 개선된 프롬프트 평가")
    print("모델: Llama-3.2-3B-Instruct")
    print("=" * 80)

    # 평가 실행
    results = evaluate_prompts()

    # 결과 분석
    best = analyze_results(results)

    # 결과 저장
    save_results(results)

    print("\n" + "=" * 80)
    print("[평가 완료]")
    print(f"최종 추천: {best['name']}")
    print(f"예상 Dacon 점수: {best['dacon_score']:.4f}")
    print("=" * 80)
