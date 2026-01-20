"""
Qwen2.5-7B-Instruct 전체 46개 샘플 테스트
최고 성능 프롬프트들로 최종 평가
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

def calculate_dacon_score(accuracy: float, prompt_length: int) -> float:
    """Dacon 점수 계산"""
    if prompt_length <= 300:
        length_score = 1.0
    else:
        length_score = math.sqrt(1 - ((prompt_length - 300) / 2700) ** 2)
    return 0.9 * accuracy + 0.1 * length_score

# 상위 성능 프롬프트들
prompts = {
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

출력: "1" 또는 "0"만""",

    "영어혼합_400자": """[Auto News] Output "1" or "0"

Automotive signals:
- OEM: Hyundai/Kia/Tesla/BMW/Mercedes
- Terms: vehicle/automotive/car-specific
- Parts: WITH car context

Non-auto (→0):
- ESS/UAM/aviation/railway
- Battery/chip WITHOUT "vehicle"

Rules:
1. Check exclusions first
2. Need explicit auto signal
3. Default = 0

자동차 명시 → 1
애매하면 → 0""",

    "V3_게이트_480자": """[자동차뉴스분류] "1" 또는 "0"만

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
모호→0"""
}

def test_full():
    """전체 샘플 테스트"""
    df = pd.read_csv('data/samples.csv')

    print(f"Qwen2.5-7B 전체 테스트")
    print(f"샘플: {len(df)}개 (자동차 {df['label'].sum()}, 비자동차 {len(df) - df['label'].sum()})")
    print("=" * 70)

    results = []

    for name, prompt in prompts.items():
        print(f"\n[{name}]")
        print(f"프롬프트 길이: {len(prompt)}자")

        correct = 0
        detailed_results = []

        start_time = time.time()

        for idx, row in df.iterrows():
            user_input = f"제목: {row['title']}\n본문: {row['content']}"
            response = call_lm_studio(prompt, user_input)

            predicted = 1 if "1" in response[:10] else 0
            actual = row['label']
            is_correct = predicted == actual

            if is_correct:
                correct += 1

            detailed_results.append({
                'id': row.get('ID', row.get('id', idx)),
                'title': row['title'][:50],
                'predicted': predicted,
                'actual': actual,
                'correct': is_correct,
                'response': response[:20]
            })

            # 진행 표시
            if (idx + 1) % 10 == 0:
                elapsed = time.time() - start_time
                print(f"  진행: {idx+1}/{len(df)} ({elapsed:.1f}초)")

        accuracy = correct / len(df)
        dacon_score = calculate_dacon_score(accuracy, len(prompt))

        # 오류 분석
        fp = sum(1 for r in detailed_results if not r['correct'] and r['actual'] == 0)
        fn = sum(1 for r in detailed_results if not r['correct'] and r['actual'] == 1)

        results.append({
            'name': name,
            'accuracy': accuracy,
            'dacon_score': dacon_score,
            'correct': correct,
            'total': len(df),
            'length': len(prompt),
            'false_positives': fp,
            'false_negatives': fn,
            'detailed_results': detailed_results
        })

        print(f"\n결과:")
        print(f"  정확도: {accuracy:.2%} ({correct}/{len(df)})")
        print(f"  예상 Dacon 점수: {dacon_score:.4f}")
        print(f"  오류: FP={fp} (0→1), FN={fn} (1→0)")

    return results

def analyze_final(results):
    """최종 분석"""
    print("\n" + "=" * 70)
    print("최종 결과 분석")
    print("=" * 70)

    # Dacon 점수 순 정렬
    sorted_results = sorted(results, key=lambda x: x['dacon_score'], reverse=True)

    print("\n[Dacon 점수 순위]")
    for i, r in enumerate(sorted_results, 1):
        print(f"{i}. {r['name']}")
        print(f"   정확도: {r['accuracy']:.2%}")
        print(f"   Dacon 점수: {r['dacon_score']:.4f}")
        print(f"   프롬프트 길이: {r['length']}자")
        print(f"   오류: FP={r['false_positives']}, FN={r['false_negatives']}")

    best = sorted_results[0]

    # 샘플별 분석
    all_results = {}
    for r in results:
        for d in r['detailed_results']:
            sid = d['id']
            if sid not in all_results:
                all_results[sid] = {
                    'title': d['title'],
                    'actual': d['actual'],
                    'correct_count': 0,
                    'predictions': []
                }
            all_results[sid]['predictions'].append({
                'prompt': r['name'],
                'predicted': d['predicted'],
                'correct': d['correct']
            })
            if d['correct']:
                all_results[sid]['correct_count'] += 1

    # 어려운 샘플 찾기
    hard_samples = [k for k, v in all_results.items() if v['correct_count'] == 0]
    easy_samples = [k for k, v in all_results.items() if v['correct_count'] == len(results)]

    print(f"\n[샘플 난이도 분석]")
    print(f"모든 프롬프트가 맞춘 샘플: {len(easy_samples)}/{len(all_results)}")
    print(f"모든 프롬프트가 틀린 샘플: {len(hard_samples)}/{len(all_results)}")

    if hard_samples:
        print("\n[가장 어려운 샘플]")
        for sid in hard_samples[:3]:
            sample = all_results[sid]
            print(f"  {sid}: {sample['title']}... (정답={sample['actual']})")

    # 최종 추천
    print("\n" + "=" * 70)
    print("최종 추천")
    print("=" * 70)
    print(f"\n최고 성능: {best['name']}")
    print(f"  Qwen2.5-7B 정확도: {best['accuracy']:.2%}")
    print(f"  예상 Dacon 점수: {best['dacon_score']:.4f}")

    if best['dacon_score'] > 0.95:
        print("\n[성공] Dacon 제출 가능한 수준!")
    elif best['dacon_score'] > 0.90:
        print("\n[양호] 괜찮은 성능, 제출 고려 가능")
    else:
        print("\n[보통] 추가 개선 필요")

    return best

def save_final_results(results, best):
    """최종 결과 저장"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # 전체 결과 저장
    with open(f'results/qwen_final_results_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 최고 프롬프트 저장
    with open('prompts/generated/best_qwen_prompt.txt', 'w', encoding='utf-8') as f:
        f.write(f"[Qwen2.5-7B 최고 성능 프롬프트]\n")
        f.write(f"이름: {best['name']}\n")
        f.write(f"정확도: {best['accuracy']:.2%}\n")
        f.write(f"예상 Dacon 점수: {best['dacon_score']:.4f}\n")
        f.write(f"프롬프트 길이: {best['length']}자\n")
        f.write(f"\n[프롬프트 내용]\n")
        f.write(prompts[best['name']])
        f.write(f"\n\n[참고]\n")
        f.write(f"Qwen2.5-7B에서 테스트됨\n")
        f.write(f"GPT-4o mini와 유사한 성능 기대\n")

    print(f"\n결과 저장 완료:")
    print(f"  - results/qwen_final_results_{timestamp}.json")
    print(f"  - prompts/generated/best_qwen_prompt.txt")

if __name__ == "__main__":
    print("=" * 70)
    print("Qwen2.5-7B 전체 샘플 최종 테스트")
    print("=" * 70)

    # 전체 테스트
    results = test_full()

    # 최종 분석
    best = analyze_final(results)

    # 결과 저장
    save_final_results(results, best)
