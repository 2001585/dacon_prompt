"""
1등 점수 0.98174에서 프롬프트 길이 역산
Dacon 공식: Score = 0.9 × accuracy + 0.1 × √(1 - (L/3000)²)
"""

import math

def calculate_possible_lengths(total_score):
    """주어진 점수에서 가능한 정확도와 길이 조합 계산"""

    print(f"목표 점수: {total_score}")
    print("=" * 60)

    results = []

    # 가능한 정확도 범위 (95% ~ 100%)
    for accuracy_pct in range(950, 1001):
        accuracy = accuracy_pct / 1000

        # 길이 점수 계산
        # total_score = 0.9 * accuracy + 0.1 * length_score
        # length_score = (total_score - 0.9 * accuracy) / 0.1
        length_score = (total_score - 0.9 * accuracy) / 0.1

        # length_score가 유효한 범위인지 확인 (0 ~ 1)
        if 0 <= length_score <= 1:
            # 길이 역산
            # length_score = sqrt(1 - (L/3000)²)
            # length_score² = 1 - (L/3000)²
            # (L/3000)² = 1 - length_score²
            # L/3000 = sqrt(1 - length_score²)
            # L = 3000 * sqrt(1 - length_score²)

            if length_score == 1:
                L = 0  # 완벽한 길이 점수
            else:
                L_ratio_squared = 1 - length_score**2
                if L_ratio_squared >= 0:
                    L = 3000 * math.sqrt(L_ratio_squared)
                else:
                    continue

            results.append({
                'accuracy': accuracy,
                'length_score': length_score,
                'length': L,
                'total': 0.9 * accuracy + 0.1 * length_score
            })

    return results

def analyze_1st_place():
    """1등 점수 분석"""
    target_score = 0.98174

    results = calculate_possible_lengths(target_score)

    print("\n가능한 정확도-길이 조합:")
    print("-" * 60)
    print("정확도   | 길이점수 | 프롬프트길이 | 최종점수")
    print("-" * 60)

    for r in results:
        # 김경태와 비슷한 정확도 강조
        highlight = "**" if 0.97 <= r['accuracy'] <= 0.99 else "  "
        print(f"{r['accuracy']:.1%} {highlight} | {r['length_score']:.4f}  | {r['length']:.0f}자      | {r['total']:.5f}")

    print("\n" + "=" * 60)
    print("핵심 시나리오 분석")
    print("=" * 60)

    # 몇 가지 주요 시나리오
    scenarios = [
        (0.98, "김경태와 비슷한 정확도"),
        (0.975, "약간 낮은 정확도"),
        (0.985, "약간 높은 정확도"),
        (0.99, "매우 높은 정확도"),
        (1.0, "완벽한 정확도 (비현실적)")
    ]

    for accuracy, desc in scenarios:
        length_score = (target_score - 0.9 * accuracy) / 0.1
        if 0 <= length_score <= 1:
            if length_score == 1:
                L = 0
            else:
                L = 3000 * math.sqrt(1 - length_score**2)

            print(f"\n[{desc}]")
            print(f"정확도: {accuracy:.1%}")
            print(f"필요 길이점수: {length_score:.4f}")
            print(f"프롬프트 길이: {L:.0f}자")

            # 김경태(591자)와 비교
            if L < 591:
                print(f"→ 김경태보다 {591-L:.0f}자 짧음")
            else:
                print(f"→ 김경태보다 {L-591:.0f}자 김")

def find_most_likely():
    """가장 가능성 높은 시나리오"""
    target_score = 0.98174

    print("\n" + "=" * 60)
    print("가장 가능성 높은 시나리오")
    print("=" * 60)

    # 김경태 정확도(98.01%)와 유사하다고 가정
    accuracy = 0.9801
    length_score = (target_score - 0.9 * accuracy) / 0.1

    print(f"\n김경태와 동일한 정확도(98.01%) 가정:")
    print(f"필요 길이점수: {length_score:.4f}")

    if length_score > 1:
        print("→ 불가능! 길이점수가 1을 초과")

        # 최대 가능 점수 계산
        max_possible = 0.9 * accuracy + 0.1 * 1.0
        print(f"98.01% 정확도의 최대 가능 점수: {max_possible:.5f}")
        print(f"1등과의 차이: {target_score - max_possible:.5f}")

        # 필요한 정확도 계산
        min_accuracy = (target_score - 0.1) / 0.9
        print(f"\n1등 점수를 위한 최소 정확도: {min_accuracy:.2%}")
    else:
        L = 3000 * math.sqrt(1 - length_score**2)
        print(f"필요 프롬프트 길이: {L:.0f}자")
        print(f"김경태(591자)보다 {591-L:.0f}자 짧아야 함")

if __name__ == "__main__":
    analyze_1st_place()
    find_most_likely()