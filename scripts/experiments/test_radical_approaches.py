"""
1등의 비밀을 찾기 위한 급진적 접근법 테스트
250자로 98% 정확도 달성 방법 탐색
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
    except:
        return "0"

def calculate_dacon_score(accuracy: float, prompt_length: int) -> float:
    """Dacon 점수 계산"""
    if prompt_length <= 300:
        length_score = 1.0
    else:
        length_score = math.sqrt(1 - ((prompt_length - 300) / 2700) ** 2)
    return 0.9 * accuracy + 0.1 * length_score

# 급진적 접근법들
radical_prompts = {
    "극한압축_200자": """[자동차]1또는0

1:현대차/기아/테슬라/BMW/벤츠/VW/도요타/GM/포드
1:차량용명시
1:전기차/수소차+생산/출시
0:ESS/UAM/항공/철도
0:배터리(차량용무)
기타:0""",

    "즉시판정_180자": """자동차→1,아니면→0

즉시1:현대차/기아/테슬라/BMW/벤츠
즉시1:차량용명시
즉시0:ESS/UAM/항공
즉시0:배터리(차량용없으면)
나머지→0""",

    "패턴매칭_210자": """[판정]1또는0

(현대차|기아|테슬라|BMW|벤츠).*(출시|생산|판매)→1
차량용.*명시→1
(ESS|UAM|항공)→0
배터리(?!차량용)→0
else→0""",

    "우선순위_220자": """자동차뉴스면1아니면0

1순위(즉시1):
완성차기업언급
차량용/자동차용명시

2순위(즉시0):
ESS/UAM/항공
배터리(차량용불명)

3순위:모두0""",

    "최소조건_170자": """[자동차]1/0

완성차→1
차량용→1
전기차생산→1
ESS/UAM→0
배터리단독→0
기타→0""",

    "자연어_240자": """자동차 관련이면 1, 아니면 0

자동차인 경우:
- 현대차,기아,테슬라,BMW,벤츠 등
- "차량용" 명시
- 전기차/수소차 생산

아닌 경우:
- ESS,UAM,항공
- 차량용 없는 배터리

애매하면 0""",

    "이진트리_190자": """[분류]1또는0

ESS/UAM있음?→0
현대차/기아있음?→1
차량용명시?→1
전기차+생산?→1
배터리+차량용무?→0
나머지→0""",

    "핵심만_150자": """자동차1아니면0

현대차기아테슬라BMW벤츠→1
차량용→1
ESS/UAM→0
배터리(차량용X)→0
기타→0""",

    "영어혼합_200자": """[Auto]1or0

1:Hyundai/Kia/Tesla/BMW/Benz
1:vehicle-specific
1:EV+production
0:ESS/UAM/aviation
0:battery(no vehicle)
else:0""",

    "수학기호없음_250자": """자동차뉴스분류 1또는0출력

1출력:
현대차 기아 테슬라 BMW 벤츠 폭스바겐 도요타 GM 언급
차량용 자동차용 명시
전기차 수소차 생산

0출력:
ESS UAM 항공 철도
차량용없는 배터리
나머지모두"""
}

def test_radical_approaches():
    """급진적 접근법 테스트"""
    df = pd.read_csv('data/samples.csv')

    # 20개 샘플만 빠른 테스트
    df_test = pd.concat([
        df[df['label'] == 1].head(10),
        df[df['label'] == 0].head(10)
    ]).reset_index(drop=True)

    print("=" * 70)
    print("1등의 비밀 찾기: 급진적 접근법 테스트")
    print("목표: 250자 이하로 98% 정확도")
    print("=" * 70)

    results = []

    for name, prompt in radical_prompts.items():
        print(f"\n[{name}]")
        print(f"길이: {len(prompt)}자")

        correct = 0
        errors = []

        for idx, row in df_test.iterrows():
            user_input = f"제목: {row['title']}\n본문: {row['content']}"
            response = call_lm_studio(prompt, user_input)

            predicted = 1 if "1" in response[:10] else 0
            actual = row['label']

            if predicted == actual:
                correct += 1
            else:
                errors.append({
                    'id': idx,
                    'predicted': predicted,
                    'actual': actual
                })

            # 진행 표시
            status = "O" if predicted == actual else "X"
            print(f"  {idx+1:2}: {status}", end="")
            if (idx + 1) % 10 == 0:
                print()

        accuracy = correct / len(df_test)
        dacon_score = calculate_dacon_score(accuracy, len(prompt))

        results.append({
            'name': name,
            'length': len(prompt),
            'accuracy': accuracy,
            'dacon_score': dacon_score,
            'correct': correct,
            'total': len(df_test),
            'errors': errors
        })

        print(f"\n정확도: {accuracy:.1%} ({correct}/{len(df_test)})")
        print(f"예상 Dacon 점수: {dacon_score:.4f}")

    return results

def analyze_radical_results(results):
    """결과 분석"""
    print("\n" + "=" * 70)
    print("급진적 접근법 분석 결과")
    print("=" * 70)

    # Dacon 점수 순 정렬
    sorted_results = sorted(results, key=lambda x: x['dacon_score'], reverse=True)

    print("\n[TOP 5 프롬프트]")
    print("-" * 70)
    print("순위 | 이름 | 길이 | 정확도 | Dacon점수")
    print("-" * 70)

    for i, r in enumerate(sorted_results[:5], 1):
        star = "⭐" if r['length'] <= 250 and r['accuracy'] >= 0.9 else ""
        print(f"{i:2}. {star} {r['name']:15} | {r['length']:3}자 | {r['accuracy']:.1%} | {r['dacon_score']:.4f}")

    # 250자 이하 중 최고 성능
    under_250 = [r for r in results if r['length'] <= 250]
    if under_250:
        best_under_250 = max(under_250, key=lambda x: x['dacon_score'])

        print(f"\n[250자 이하 최고 성능]")
        print(f"프롬프트: {best_under_250['name']}")
        print(f"길이: {best_under_250['length']}자")
        print(f"정확도: {best_under_250['accuracy']:.1%}")
        print(f"Dacon 점수: {best_under_250['dacon_score']:.4f}")

        if best_under_250['accuracy'] >= 0.9:
            print("\n🎉 성공! 250자 이하로 90%+ 달성!")
            print("→ 전체 46개 샘플로 확대 테스트 필요")
        else:
            print("\n⚠️ 아직 부족. 다른 접근 필요")

    # 가장 짧은 고성능
    high_perf = [r for r in results if r['accuracy'] >= 0.8]
    if high_perf:
        shortest_high = min(high_perf, key=lambda x: x['length'])
        print(f"\n[80%+ 정확도 중 가장 짧은]")
        print(f"프롬프트: {shortest_high['name']}")
        print(f"길이: {shortest_high['length']}자")
        print(f"정확도: {shortest_high['accuracy']:.1%}")

def main():
    # 테스트 실행
    results = test_radical_approaches()

    # 결과 분석
    analyze_radical_results(results)

    # 최종 권장사항
    print("\n" + "=" * 70)
    print("최종 분석")
    print("=" * 70)

    print("""
[1등의 비밀 추정]
1. 점수 계산 없이 즉시 판정
2. 수학 기호 없이 자연어/기호
3. 극도로 압축된 조건문
4. 디폴트 0 명확화
5. 핵심 브랜드만 유지

[핵심 통찰]
- 김경태: 정교하지만 길다 (591자)
- 1등: 단순하지만 효과적 (250자)
- 차이: 접근법이 완전히 다름!
""")

if __name__ == "__main__":
    main()