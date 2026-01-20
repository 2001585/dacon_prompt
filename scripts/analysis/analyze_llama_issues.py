"""
Llama-3.2 문제점 심층 분석
왜 자동차 샘플을 0으로 분류하는지 파악
"""

import json
import pandas as pd

def analyze_failures():
    """실패 패턴 분석"""
    # 결과 파일 로드
    with open('results/local_llm_results_Llama-3.2-3B-Instruct-GGUF_20250915_165743.json', 'r', encoding='utf-8') as f:
        results = json.load(f)

    # 김경태 원본 결과 분석
    kimgyeongtae = results[0]  # 첫 번째가 김경태 원본

    print("=" * 80)
    print("Llama-3.2 문제점 분석")
    print("=" * 80)

    print(f"\n김경태 원본 프롬프트 성능:")
    print(f"  정확도: {kimgyeongtae['accuracy']:.1%}")
    print(f"  정답: {kimgyeongtae['correct']}/46")

    # 실패 유형 분석
    false_positives = []  # 0인데 1로 예측 (과잉)
    false_negatives = []  # 1인데 0으로 예측 (미탐)

    for sample in kimgyeongtae['detailed_results']:
        if not sample['correct']:
            if sample['actual'] == 0 and sample['predicted'] == 1:
                false_positives.append(sample)
            elif sample['actual'] == 1 and sample['predicted'] == 0:
                false_negatives.append(sample)

    print(f"\n[오류 유형 분석]")
    print(f"  False Positive (0→1): {len(false_positives)}개")
    print(f"  False Negative (1→0): {len(false_negatives)}개")

    # False Negative가 많다면 문제
    if false_negatives:
        print(f"\n[심각] 자동차 뉴스를 비자동차로 분류한 경우: {len(false_negatives)}개")
        for fn in false_negatives[:5]:
            print(f"  - {fn['id']}: {fn['title'][:50]}...")

    # 모든 프롬프트 결과 비교
    print("\n" + "=" * 80)
    print("모든 프롬프트 성능 비교")
    print("=" * 80)

    for r in results:
        print(f"\n{r['name']}:")
        print(f"  정확도: {r['accuracy']:.1%} ({r['correct']}/46)")

        # 이 프롬프트의 오류 유형
        fp = 0
        fn = 0
        for sample in r['detailed_results']:
            if not sample['correct']:
                if sample['actual'] == 0 and sample['predicted'] == 1:
                    fp += 1
                elif sample['actual'] == 1 and sample['predicted'] == 0:
                    fn += 1

        print(f"  오류: FP={fp} (0→1), FN={fn} (1→0)")

    # 패턴 발견
    print("\n" + "=" * 80)
    print("[핵심 발견]")
    print("=" * 80)

    # 대부분 1로 예측하는 경향
    total_1_predictions = sum(1 for s in kimgyeongtae['detailed_results'] if s['predicted'] == 1)
    print(f"\n김경태 프롬프트의 예측 분포:")
    print(f"  1로 예측: {total_1_predictions}/46 ({total_1_predictions/46:.1%})")
    print(f"  0으로 예측: {46-total_1_predictions}/46 ({(46-total_1_predictions)/46:.1%})")

    # 실제 라벨 분포
    df = pd.read_csv('data/samples.csv')
    actual_1 = df['label'].sum()
    actual_0 = len(df) - actual_1
    print(f"\n실제 라벨 분포:")
    print(f"  자동차(1): {actual_1}/46 ({actual_1/46:.1%})")
    print(f"  비자동차(0): {actual_0}/46 ({actual_0/46:.1%})")

    print("\n[문제 진단]")
    print("Llama-3.2는 대부분을 1(자동차)로 예측하는 경향이 있음")
    print("→ 게이트 조건이나 음수 점수가 제대로 작동하지 않음")
    print("→ 더 명확하고 단순한 규칙이 필요")

def find_working_patterns():
    """어떤 샘플이 잘 작동하는지 찾기"""
    with open('results/local_llm_results_Llama-3.2-3B-Instruct-GGUF_20250915_165743.json', 'r', encoding='utf-8') as f:
        results = json.load(f)

    df = pd.read_csv('data/samples.csv')

    print("\n" + "=" * 80)
    print("성공 패턴 분석")
    print("=" * 80)

    # 모든 프롬프트가 맞춘 샘플
    all_correct_ids = []
    first_prompt = results[0]

    for sample in first_prompt['detailed_results']:
        sample_id = sample['id']
        all_correct = True

        # 모든 프롬프트에서 체크
        for r in results:
            for s in r['detailed_results']:
                if s['id'] == sample_id and not s['correct']:
                    all_correct = False
                    break

        if all_correct:
            all_correct_ids.append(sample_id)

    print(f"\n모든 프롬프트가 맞춘 샘플: {len(all_correct_ids)}개")
    for sid in all_correct_ids:
        sample = df[df.get('ID', df.get('id')) == sid].iloc[0]
        print(f"  {sid}: {sample['title'][:50]}... (라벨={sample['label']})")

    # 모든 프롬프트가 틀린 샘플
    all_wrong_ids = []
    for sample in first_prompt['detailed_results']:
        sample_id = sample['id']
        all_wrong = True

        for r in results:
            for s in r['detailed_results']:
                if s['id'] == sample_id and s['correct']:
                    all_wrong = False
                    break

        if all_wrong:
            all_wrong_ids.append(sample_id)

    print(f"\n모든 프롬프트가 틀린 샘플: {len(all_wrong_ids)}개")
    for sid in all_wrong_ids[:5]:
        for s in first_prompt['detailed_results']:
            if s['id'] == sid:
                print(f"  {sid}: {s['title'][:50]}... (정답={s['actual']}, 예측={s['predicted']})")
                break

def suggest_improvements():
    """개선 방안 제안"""
    print("\n" + "=" * 80)
    print("개선 방안")
    print("=" * 80)

    print("""
[문제점]
1. Llama-3.2는 복잡한 조건문을 잘 이해하지 못함
2. 대부분을 1(자동차)로 분류하는 과잉 일반화
3. 음수 점수나 게이트 조건이 작동하지 않음

[해결책]
1. 더 단순하고 명확한 규칙 사용
2. "0이 기본값"으로 설정하고 자동차일 때만 1
3. 부정 조건을 먼저 체크 (ESS/UAM 즉시 0)
4. 영어 키워드 활용 (Llama는 영어에 더 강함)

[추천 프롬프트 방향]
```
Classification: Automotive news = 1, Others = 0

Immediate 0 if: ESS, UAM, aviation, railway, policy-only
Immediate 1 if: Hyundai, Kia, Tesla, BMW, Mercedes

Check for "vehicle" or "automotive" explicitly mentioned.
Default to 0 if unclear.

Output only "1" or "0"
```
""")

if __name__ == "__main__":
    analyze_failures()
    find_working_patterns()
    suggest_improvements()
