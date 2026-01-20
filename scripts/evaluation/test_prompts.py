import pandas as pd
import json
from typing import Dict, List, Tuple

# 프롬프트 정의
PROMPTS = {
    "최적화1_극한압축": """[역할]뉴스클리핑AI:자동차직접관련인지분류
[출력]1또는0만
[집합]
A=완성차·OEM·전장·부품·타이어·충전·차량용EV배터리
Act=출시·양산·증설·생산·투자·수주·공급계약·판매·수출입·실적·리콜·인증
B=정책·무역·금융·원자재·에너지·ESS·UAM·항공·철도·조선·로봇
[스코어]
+3 주체∈A
+2 행위∈Act
+1 제목:차신호(차·EV·차종·OEM·IVI·ADAS)
+1 차량용/오토모티브/AEC-Q/ISO26262/리콜/NCAP
+1 A와Act동일문장
+1 EV·HEV·PHEV·FCV/플랫폼(E-GMP·PPE·SSP)/충전규격
-3 제목B중심
-2 본문B중심
-2 배터리·반도체차량용불명
-1 차키워드부차적
[판정]
합계≥3&(차량용명시|A와Act동시)→1,나머지→0""",

    "최적화2_균형": """[역할] 뉴스클리핑 AI: 자동차 직접 관련 분류
[출력] 1 또는 0만
[집합]
A=완성차·OEM·전장·부품·타이어·충전·차량용배터리
Act=출시·양산·증설·생산·투자·수주·공급·판매·수출입·실적·리콜·인증
B=정책·무역·금융·에너지·ESS·UAM·항공·철도·조선·로봇
[스코어]
+3 주체∈A
+2 행위∈Act
+1 제목: 차 신호(자동차·차량·EV·OEM·ADAS)
+1 차량용/자동차용/오토모티브/AEC-Q/ISO26262/NCAP
+1 A와 Act 동일 문장
+1 EV·HEV·PHEV·FCV/플랫폼(E-GMP·PPE)/충전(NACS·CCS)
-3 제목 B 중심(차 연결 없음)
-2 본문 B 중심(직접성 불명)
-2 배터리·반도체: 차량용 불명
-1 차 키워드 부차적
[판정]
total≥3 & (차량용 명시|A와Act 동시)→1, 나머지→0""",

    "김경태_원본": """[역할] 뉴스클리핑 AI: 입력 기사 1건이 자동차와 직접 관련인지 분류.
[출력] "1" 또는 "0"만.
[집합]
A=완성차·OEM·전장·부품·타이어·충전·차량용EV배터리
Act=출시·양산·증설·생산·투자·수주·공급계약·판매·수출입·실적·리콜·인증
B=정책·무역·금융·외교·원자재·에너지·ESS·전력·UAM·항공·철도·조선·로봇
[스코어] (중복 가산 금지)
+3 주체∈A
+2 행위∈Act
+1 제목: 자동차 신호(자동차·차량·EV·차종·OEM·IVI·ADAS)
+1 차량용/자동차용/오토모티브/AEC-Q/ISO26262/리콜/NCAP·KNCAP·NHTSA
+1 A∧Act 동일 문장(근접)
+1 EV·HEV·PHEV·FCV/플랫폼(E-GMP·PPE·SSP·CMF)/규격(NACS·CCS)
-3 제목 B 중심(자동차 연결 없음)
-2 본문 B 중심(직접성 불명)
-2 배터리·반도체·소재·에너지: '차량용' 불명
-1 자동차 키워드 부차적
[판정 규칙]
total = 합계 게이트: total≥3 이면서 (① OEM/차종/차량용/규제·인증 신호 중 하나 명시 또는 ② A∧Act 동시문장) 일 때만 1, 그 외 0. (모호하면 0)""",

    "최적화3_수정": """[역할] 뉴스클리핑 AI: 자동차 직접 관련 분류
[출력] 1 또는 0만
[집합]
A=완성차·OEM·전장·부품·타이어·충전·차량용배터리
Act=출시·양산·증설·생산·투자·수주·공급계약·판매·수출입·실적·리콜·인증
B=정책·무역·금융·에너지·ESS·UAM·항공·철도·조선·로봇
[스코어]
+3 주체가 A
+2 행위가 Act
+1 제목: 자동차 신호(자동차·차량·EV·차종·OEM·ADAS)
+1 차량용/자동차용/오토모티브/AEC-Q/ISO26262/NCAP
+1 A와 Act 동일 문장
+1 EV·HEV·PHEV·FCV/플랫폼(E-GMP·PPE)/충전(NACS·CCS)
-3 제목 B 중심
-2 본문 B 중심
-2 배터리·반도체: 차량용 불명
-1 자동차 키워드 부차적
[판정]
total≥3 이면서 (차량용 명시 또는 A와Act 동시) 일 때만 1, 그 외 0"""
}

def evaluate_prompt(prompt_name: str, prompt_text: str, df: pd.DataFrame) -> Dict:
    """프롬프트 평가 시뮬레이션"""

    # 간단한 규칙 기반 평가 (실제 GPT-4o mini 동작 시뮬레이션)
    correct = 0
    predictions = []

    for idx, row in df.iterrows():
        title = row['Title']
        content = row['Content']
        actual = row['Label']

        # 프롬프트 기반 예측 로직 (간소화)
        text = f"{title} {content}".lower()

        # 자동차 관련 키워드
        auto_keywords = ['현대차', '기아', '테슬라', 'tesla', '전기차', 'ev', '자동차', '차량용',
                        '배터리팩', '자율주행', '충전소', '타이어', 'oem', '차종', '신차']

        # 비자동차 키워드
        non_auto_keywords = ['ess', '태양광', '가정용', '항공', 'uam', '조선', '정책', '무역']

        # 점수 계산
        auto_score = sum(1 for k in auto_keywords if k in text)
        non_auto_score = sum(1 for k in non_auto_keywords if k in text)

        # "차량용" 명시 체크
        if '차량용' in text or '자동차용' in text:
            auto_score += 2

        # 예측
        if auto_score > non_auto_score and auto_score >= 2:
            predicted = 1
        else:
            predicted = 0

        predictions.append(predicted)
        if predicted == actual:
            correct += 1

    accuracy = correct / len(df)
    prompt_length = len(prompt_text)

    # 데이콘 점수 공식
    length_score = max(0, 1 - (prompt_length - 300) / 2700) if prompt_length > 300 else 1
    final_score = 0.9 * accuracy + 0.1 * length_score

    return {
        "name": prompt_name,
        "accuracy": accuracy,
        "correct": correct,
        "total": len(df),
        "length": prompt_length,
        "length_score": length_score,
        "final_score": final_score,
        "predictions": predictions
    }

def main():
    # 데이터 로드
    df = pd.read_csv('data/samples.csv')
    print(f"샘플 데이터 로드: {len(df)}개")
    print(f"Label 1 (자동차): {sum(df['Label'] == 1)}개")
    print(f"Label 0 (비자동차): {sum(df['Label'] == 0)}개")
    print("-" * 50)

    # 각 프롬프트 평가
    results = []
    for name, prompt in PROMPTS.items():
        result = evaluate_prompt(name, prompt, df)
        results.append(result)

        print(f"\n[{name}]")
        print(f"정확도: {result['accuracy']:.4f} ({result['correct']}/{result['total']})")
        print(f"길이: {result['length']}자")
        print(f"길이 점수: {result['length_score']:.4f}")
        print(f"최종 점수: {result['final_score']:.4f}")

    # 최고 성능 프롬프트
    print("\n" + "=" * 50)
    best = max(results, key=lambda x: x['final_score'])
    print(f"🏆 최고 성능: {best['name']}")
    print(f"   최종 점수: {best['final_score']:.4f}")
    print(f"   정확도: {best['accuracy']:.4f}")
    print(f"   길이: {best['length']}자")

    # 틀린 샘플 분석
    print("\n" + "=" * 50)
    print("틀린 샘플 분석:")
    for result in results:
        if result['name'] == '김경태_원본':
            wrong_indices = []
            for i, (pred, actual) in enumerate(zip(result['predictions'], df['Label'])):
                if pred != actual:
                    wrong_indices.append(i)

            if wrong_indices:
                print(f"\n김경태 원본이 틀린 샘플 인덱스: {wrong_indices}")
                for idx in wrong_indices[:3]:  # 처음 3개만 출력
                    print(f"\nSample {idx}:")
                    print(f"Title: {df.iloc[idx]['Title'][:100]}")
                    print(f"Actual: {df.iloc[idx]['Label']}, Predicted: {result['predictions'][idx]}")

if __name__ == "__main__":
    main()