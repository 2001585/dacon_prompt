"""
0.98+ 목표 안전한 프롬프트들
김경태 원본의 핵심 유지 + 과적합 방지
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

# 김경태 원본 핵심만 추출한 버전들
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

    "게이트조건_강화_550자": """[자동차뉴스분류]점수계산후"1"또는"0"

A={현대차,기아,테슬라,벤츠,BMW,폭스바겐,도요타,혼다,포드,GM,스텔란티스,리비안,BYD,니오}
B={자동차,자율주행,전기차,수소차}
Act={출시,양산,판매,수주,계약,공급,생산,투자,인수,협력,개발}

점수:
+3 제목이나본문주어가A
+2 제목이B
+1 본문이B
+2 Act등장
+1 OEM/완성차언급
+1 차량용/자동차용명시
+1 A와Act동일문장
-3 제목B중심(차연결없음)
-2 본문B중심(직접성불명)
-2 배터리반도체인데차량용불명

판정:점수3이상이고(OEM/차량용명시또는A와Act동시)일때만1,나머지0
모호하면0""",

    "핵심만_500자": """[자동차뉴스]점수후"1"또는"0"

완성차={현대차,기아,테슬라,BMW,벤츠,폭스바겐,도요타,포드,GM,BYD}
행위={출시,양산,판매,수주,생산,투자,계약,공급}

점수:
+3 완성차주체
+2 자동차/전기차/수소차제목
+2 행위포함
+1 차량용명시
+1 완성차와행위동시
-3 ESS/UAM/항공/철도
-2 배터리반도체차량용불명

판정:
점수3이상+(차량용명시or완성차행위동시)→1
나머지→0""",

    "더간단_450자": """[자동차분류]"1"또는"0"

완성차:현대차/기아/테슬라/BMW/벤츠/폭스바겐/도요타/GM/포드
자동차단어:자동차/전기차/수소차/자율주행
자동차행위:출시/양산/판매/생산/투자

점수:
+3 완성차언급
+2 자동차단어
+2 자동차행위
+1 차량용명시
-3 ESS/UAM/항공
-2 배터리차량용불명

최종:점수3이상이고(차량용또는완성차+행위)→1
아니면→0""",

    "안전버전_수식제거_591자": """[자동차뉴스분류기준]점수계산후"1"또는"0"출력

집합정의:
A={현대차,기아,르노,쉐보레,테슬라,벤츠,BMW,폭스바겐,도요타,혼다,포드,GM,스텔란티스,리비안,루시드,BYD,니오,샤오펑,리상}
B={모빌리티,자동차,자율주행,전기차,수소차,하이브리드}
Act={출시,양산,판매,수주,계약,공급,생산,증산,감산,투자,인수,합병,협력,제휴,개발}

점수계산:
+3 제목이나본문주어가A에속함
+2 제목이B에속함
+1 본문이B에속함
+2 Act등장
+1 OEM/완성차/차종언급
+1 차량용/규제인증(ADAS,NCAP,UNECE,AEC-Q,ISO26262)
+1 A와Act동일문장
-3 제목B중심(자동차연결없음)
-2 본문B중심(직접성불명)
-2 배터리반도체소재에너지인데차량용불명

판정:total이3이상이고(OEM/차종/차량용/규제인증중하나또는A와Act동시)일때만1,나머지0"""
}

def test_safe_prompts():
    """안전한 프롬프트 테스트"""
    df = pd.read_csv('data/samples.csv')

    print("0.98+ 목표 안전한 프롬프트 테스트")
    print(f"샘플: {len(df)}개")
    print("=" * 70)

    results = []

    for name, prompt in prompts.items():
        print(f"\n[{name}]")
        print(f"길이: {len(prompt)}자")

        correct = 0
        errors = []

        start_time = time.time()

        for idx, row in df.iterrows():
            user_input = f"제목: {row['title']}\n본문: {row['content']}"
            response = call_lm_studio(prompt, user_input)

            predicted = 1 if "1" in response[:10] else 0
            actual = row['label']

            if predicted == actual:
                correct += 1
            else:
                errors.append({
                    'id': row.get('ID', idx),
                    'title': row['title'][:40],
                    'predicted': predicted,
                    'actual': actual
                })

            if (idx + 1) % 10 == 0:
                print(f"  진행: {idx+1}/{len(df)}")

        accuracy = correct / len(df)
        dacon_score = calculate_dacon_score(accuracy, len(prompt))

        # 오류 유형 분석
        fp = sum(1 for e in errors if e['actual'] == 0)
        fn = sum(1 for e in errors if e['actual'] == 1)

        results.append({
            'name': name,
            'accuracy': accuracy,
            'dacon_score': dacon_score,
            'length': len(prompt),
            'correct': correct,
            'total': len(df),
            'false_positives': fp,
            'false_negatives': fn,
            'errors': errors
        })

        print(f"\n결과:")
        print(f"  정확도: {accuracy:.2%} ({correct}/{len(df)})")
        print(f"  예상 Dacon 점수: {dacon_score:.4f}")
        print(f"  오류: FP={fp}, FN={fn}")

        elapsed = time.time() - start_time
        print(f"  소요시간: {elapsed:.1f}초")

    return results

def analyze_safety(results):
    """과적합 위험 분석"""
    print("\n" + "=" * 70)
    print("과적합 위험 분석")
    print("=" * 70)

    # 0.98 이상 프롬프트
    high_score = [r for r in results if r['dacon_score'] >= 0.98]

    if high_score:
        print("\n[0.98+ 달성 프롬프트]")
        for r in sorted(high_score, key=lambda x: x['length']):
            print(f"  {r['name']}")
            print(f"    Dacon 점수: {r['dacon_score']:.4f}")
            print(f"    길이: {r['length']}자")
            print(f"    정확도: {r['accuracy']:.2%}")

    # 길이별 정렬
    print("\n[길이 순 정렬 (짧은 순)]")
    for r in sorted(results, key=lambda x: x['length']):
        status = "✓" if r['dacon_score'] >= 0.98 else " "
        print(f"  [{status}] {r['length']:3}자: {r['name']} (점수={r['dacon_score']:.4f})")

    # 추천
    print("\n[최종 추천]")

    # 0.98 이상 중 가장 짧은 것
    if high_score:
        best = min(high_score, key=lambda x: x['length'])
        print(f"1순위: {best['name']}")
        print(f"  - 예상 점수: {best['dacon_score']:.4f}")
        print(f"  - 길이: {best['length']}자")
        print(f"  - 김경태 원본 대비 {591 - best['length']}자 단축")

    # 김경태 원본
    original = next((r for r in results if "원본" in r['name']), None)
    if original:
        print(f"\n안전: 김경태 원본")
        print(f"  - 검증된 점수: 0.9801")
        print(f"  - 실제 Dacon에서 검증됨")

def save_recommendations(results):
    """최종 권장사항 저장"""
    with open('docs/recommendations/final_safe_recommendations.md', 'w', encoding='utf-8') as f:
        f.write("# 0.98+ 목표 최종 권장 프롬프트\n\n")
        f.write("## ⚠️ 과적합 주의사항\n")
        f.write("- 46개 샘플은 매우 적음\n")
        f.write("- 로컬 테스트와 실제 Dacon 점수는 다를 수 있음\n")
        f.write("- 김경태 원본이 가장 안전한 선택\n\n")

        f.write("## 🎯 제출 전략\n\n")

        # 0.98+ 프롬프트들
        high_score = [r for r in results if r['dacon_score'] >= 0.98]
        if high_score:
            best = min(high_score, key=lambda x: x['length'])
            f.write(f"### 1순위: {best['name']} ({best['length']}자)\n")
            f.write(f"- 예상 점수: {best['dacon_score']:.4f}\n")
            f.write(f"- 정확도: {best['accuracy']:.2%}\n")
            f.write(f"- 프롬프트:\n```\n{prompts[best['name']]}\n```\n\n")

        f.write("### 안전: 김경태 원본 (591자)\n")
        f.write("- 실제 검증 점수: 0.9801\n")
        f.write("- 가장 안전한 선택\n\n")

        f.write("## 📊 테스트 결과\n\n")
        f.write("| 프롬프트 | 길이 | 정확도 | 예상 점수 |\n")
        f.write("|---------|------|--------|----------|\n")
        for r in sorted(results, key=lambda x: x['dacon_score'], reverse=True):
            f.write(f"| {r['name']} | {r['length']}자 | {r['accuracy']:.2%} | {r['dacon_score']:.4f} |\n")

    print("\n결과 저장: docs/recommendations/final_safe_recommendations.md")

if __name__ == "__main__":
    # 테스트
    results = test_safe_prompts()

    # 분석
    analyze_safety(results)

    # 저장
    save_recommendations(results)
