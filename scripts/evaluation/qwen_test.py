"""
Qwen2.5-7B-Instruct 모델로 프롬프트 테스트
GPT-4o mini와 유사한 성능 기대
"""

import pandas as pd
import requests
import json
import time
import math

def call_lm_studio(prompt: str, user_input: str) -> str:
    """LM Studio API 호출 - Qwen2.5-7B"""
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
        print(f"    API 에러: {e}")
        return "0"

def calculate_dacon_score(accuracy: float, prompt_length: int) -> float:
    """Dacon 점수 계산"""
    if prompt_length <= 300:
        length_score = 1.0
    else:
        length_score = math.sqrt(1 - ((prompt_length - 300) / 2700) ** 2)
    return 0.9 * accuracy + 0.1 * length_score

# 핵심 프롬프트들
prompts = {
    "김경태_원본_591자": """[자동차뉴스분류기준]점수계산후"1"또는"0"출력

집합정의:
A={현대차,기아,르노,쉐보레,테슬라,벤츠,BMW,폭스바겐,도요타,혼다,포드,GM,스텔란티스,리비안,루시드,BYD,니오,샤오펑,리상}
B={모빌리티,자동차,자율주행,전기차,수소차,하이브리드}
Act={출시,양산,판매,수주,계약,공급,생산,증산,감산,투자,인수,합병,협력,제휴,개발}

점수계산:
+3 (제목∈A)∨(본문주어∈A)
+2 제목∈B
+1 본문∈B
+2 Act등장
+1 OEM/완성차/차종언급
+1 차량용/규제·인증(ADAS,NCAP,UNECE,AEC-Q,ISO26262)
+1 A∧Act동일문장(근접)
-3 제목B중심(자동차연결없음)
-2 본문B중심(직접성불명)
-2 배터리·반도체·소재·에너지:'차량용'불명

판정: total≥3이면서(①OEM/차종/차량용/규제·인증신호중하나명시또는②A∧Act동시문장)일때만1,나머지0""",

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
애매하면 → 0"""
}

def test_qwen():
    """Qwen 모델 테스트"""
    df = pd.read_csv('data/samples.csv')

    # 20개 샘플로 빠른 테스트
    df_test = pd.concat([
        df[df['label'] == 1].head(10),  # 자동차 10개
        df[df['label'] == 0].head(10)   # 비자동차 10개
    ]).reset_index(drop=True)

    print(f"Qwen2.5-7B-Instruct 테스트")
    print(f"샘플: {len(df_test)}개 (자동차 10, 비자동차 10)")
    print("=" * 70)

    results = []

    for name, prompt in prompts.items():
        print(f"\n[{name}]")
        print(f"프롬프트 길이: {len(prompt)}자")

        correct = 0
        errors = []
        predictions = []

        start_time = time.time()

        for idx, row in df_test.iterrows():
            user_input = f"제목: {row['title']}\n본문: {row['content']}"
            response = call_lm_studio(prompt, user_input)

            # 예측값 추출
            predicted = 1 if "1" in response[:10] else 0
            actual = row['label']
            is_correct = predicted == actual

            if is_correct:
                correct += 1
            else:
                errors.append({
                    'id': row.get('ID', row.get('id', idx)),
                    'title': row['title'][:40],
                    'predicted': predicted,
                    'actual': actual
                })

            predictions.append({
                'predicted': predicted,
                'actual': actual,
                'correct': is_correct
            })

            # 진행 표시
            status = "O" if is_correct else "X"
            print(f"  {idx+1:2}: {status}", end="")
            if (idx + 1) % 10 == 0:
                print()

        elapsed = time.time() - start_time
        accuracy = correct / len(df_test)
        dacon_score = calculate_dacon_score(accuracy, len(prompt))

        results.append({
            'name': name,
            'accuracy': accuracy,
            'dacon_score': dacon_score,
            'correct': correct,
            'total': len(df_test),
            'length': len(prompt),
            'time': elapsed,
            'errors': errors,
            'predictions': predictions
        })

        print(f"\n  정확도: {accuracy:.1%} ({correct}/{len(df_test)})")
        print(f"  예상 Dacon 점수: {dacon_score:.4f}")
        print(f"  소요 시간: {elapsed:.1f}초")

        # 오류 분석
        if errors:
            fp = sum(1 for e in errors if e['actual'] == 0 and e['predicted'] == 1)
            fn = sum(1 for e in errors if e['actual'] == 1 and e['predicted'] == 0)
            print(f"  오류: FP={fp} (0→1), FN={fn} (1→0)")

    return results

def analyze_results(results):
    """결과 분석"""
    print("\n" + "=" * 70)
    print("Qwen2.5-7B 결과 분석")
    print("=" * 70)

    # 정확도 순 정렬
    sorted_results = sorted(results, key=lambda x: x['accuracy'], reverse=True)

    print("\n[정확도 순위]")
    for i, r in enumerate(sorted_results, 1):
        print(f"{i}. {r['name']}")
        print(f"   정확도: {r['accuracy']:.1%} ({r['correct']}/{r['total']})")
        print(f"   Dacon 점수: {r['dacon_score']:.4f}")
        print(f"   프롬프트 길이: {r['length']}자")

    # 최고 성능
    best = sorted_results[0]

    print(f"\n[최고 성능: {best['name']}]")
    print(f"  정확도: {best['accuracy']:.1%}")
    print(f"  예상 Dacon 점수: {best['dacon_score']:.4f}")

    # Llama-3.2와 비교
    print("\n[모델 비교]")
    print("Llama-3.2-3B: 약 55% 정확도")
    print(f"Qwen2.5-7B: {best['accuracy']:.1%} 정확도")

    if best['accuracy'] > 0.7:
        print("\n✅ Qwen이 Llama보다 훨씬 우수한 성능!")
        print("→ 전체 46개 샘플로 확장 테스트 권장")
    elif best['accuracy'] > 0.6:
        print("\n⚠️ Qwen이 약간 나은 성능")
        print("→ 프롬프트 개선 필요")
    else:
        print("\n❌ Qwen도 성능 부족")
        print("→ 다른 모델 시도 필요")

    # 샘플별 성공률
    sample_success = {}
    for r in results:
        for i, p in enumerate(r['predictions']):
            if i not in sample_success:
                sample_success[i] = {'correct': 0, 'total': 0}
            sample_success[i]['total'] += 1
            if p['correct']:
                sample_success[i]['correct'] += 1

    all_correct = sum(1 for v in sample_success.values() if v['correct'] == v['total'])
    all_wrong = sum(1 for v in sample_success.values() if v['correct'] == 0)

    print(f"\n[샘플 분석]")
    print(f"모든 프롬프트가 맞춘 샘플: {all_correct}/20")
    print(f"모든 프롬프트가 틀린 샘플: {all_wrong}/20")

    return best

def save_results(results):
    """결과 저장"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"results/qwen_test_results_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {filename}")

if __name__ == "__main__":
    print("=" * 70)
    print("Qwen2.5-7B-Instruct 프롬프트 테스트")
    print("=" * 70)

    # 테스트 실행
    results = test_qwen()

    # 결과 분석
    best = analyze_results(results)

    # 결과 저장
    save_results(results)

    print("\n" + "=" * 70)
    print("테스트 완료")
    print("=" * 70)
