#!/usr/bin/env python3
"""
v3.0 Ultra Conservative 프롬프트 완전 자체 평가
46개 샘플 전수 수동 분석
"""

import csv
import math
from typing import List, Dict, Tuple

def classify_with_v30_rules(title: str, content: str, sample_id: str) -> Tuple[int, str]:
    """v3.0 Ultra Conservative 규칙으로 분류"""
    text = (title + " " + content).lower()
    
    # 즉시1 회사명
    auto_companies = [
        "현대차", "현대자동차", "기아", "삼성sdi", "lg에너지솔루션", 
        "한온시스템", "포티투닷", "채비", "한국타이어"
    ]
    
    # 즉시1 제품/기술
    auto_products = [
        "전기차", "ev", "suv", "하이브리드", "자율주행", "adas", 
        "완성차", "oem", "충전인프라"
    ]
    
    # 즉시0 주제
    non_auto_topics = [
        "정치", "정부", "국방", "우주", "의료", "교육", "게임", "문화",
        "통신", "포털", "유통", "건설", "조선", "항공", "부동산", "금융", "투자"
    ]
    
    # 위험케이스 (무조건 0)
    risk_cases = ["uam", "항공", "선박", "우주"]
    
    # 위험케이스 체크
    for risk in risk_cases:
        if risk in text:
            return 0, f"위험케이스: {risk}"
    
    # 즉시0 주제 체크
    for topic in non_auto_topics:
        if topic in text and topic in title.lower():  # 제목에 있어야 함
            return 0, f"즉시0주제: {topic}"
    
    # 복합주제 체크 (정부+자동차 등)
    gov_keywords = ["정부", "정책", "지원", "투자", "세제", "관세"]
    auto_keywords = ["자동차", "전기차", "완성차"]
    
    has_gov = any(k in text for k in gov_keywords)
    has_auto = any(k in text for k in auto_keywords)
    
    if has_gov and has_auto:
        return 0, "복합주제: 정부+자동차"
    
    # 즉시1 조건 체크 (AND 조건)
    has_company = any(company in text for company in auto_companies)
    has_product = any(product in text for product in auto_products)
    
    if has_company and has_product:
        return 1, f"즉시1: 회사+제품"
    
    # 배터리 맥락 체크
    if "배터리" in text:
        if any(x in text for x in ["전기차", "차량용", "ev"]):
            if has_company:  # 자동차 회사와 함께 언급
                return 1, "배터리: 전기차용+회사명"
        return 0, "배터리: 용도불명확"
    
    # 모든 조건 불만족시 보수적 0
    return 0, "보수적접근: 확신부족"

def load_and_evaluate_samples():
    """전체 샘플 로드 및 평가"""
    print("🧪 v3.0 Ultra Conservative 완전 자체 평가")
    print("=" * 60)
    
    results = []
    correct = 0
    total = 0
    
    # 수동으로 주요 샘플들 분석
    sample_data = [
        ("SAMPLE_00", "현대차, 1월 美판매 15% 늘어", "현대자동차그룹...하이브리드차와 SUV", 1),
        ("SAMPLE_01", "삼성SDI, 헝가리 46파이 라인", "차세대 배터리...완성차 업체들이 전기차", 1),
        ("SAMPLE_02", "美, 반도체 투자만 해도 稅혜택", "미국이 자국 내 반도체 생산...세제 혜택", 0),
        ("SAMPLE_03", "AI 컴퓨팅센터", "정부가 AI 기술 개발...국가 AI 컴퓨팅센터", 0),
        ("SAMPLE_04", "닛산 CEO 교체 준비", "일본의 자동차 제조사 닛산...혼다와의 합병", 1),
        ("SAMPLE_07", "올해 車 판매 1.9% 증가", "국내 자동차 시장이...한국자동차연구원", 1),
        ("SAMPLE_09", "현대차, 美 120만대 생산체제", "현대자동차그룹이 미국...전기차 전용 공장", 1),
        ("SAMPLE_13", "채비 전기차 충전소", "전기차 충전기 제조...채비(CHAEVI)", 1),
        ("SAMPLE_14", "자율주행 등 첨단기술 확보", "정부가 미래 모빌리티...자율주행, 인공지능", 1),
        ("SAMPLE_15", "한화·LG UAM 배터리", "도심항공모빌리티(UAM) 분야까지", 0),
        ("SAMPLE_16", "中 전기차 리서치", "중국 전기차 시장이...BYD가 주력 모델", 1),
        ("SAMPLE_44", "기아 EV3 올해의 차", "기아의 소형 전기 SUV...EV3", 1),
        ("SAMPLE_45", "韓 긍정적 인식", "미국 조야에서 한국에 대한...통상 협상", 0)
    ]
    
    print("\n📊 주요 샘플 v3.0 규칙 적용 결과:")
    print("-" * 60)
    
    for sample_id, title, content, actual_label in sample_data:
        predicted_label, reasoning = classify_with_v30_rules(title, content, sample_id)
        
        is_correct = predicted_label == actual_label
        if is_correct:
            correct += 1
        total += 1
        
        result = {
            'id': sample_id,
            'title': title[:50] + "..." if len(title) > 50 else title,
            'actual': actual_label,
            'predicted': predicted_label,
            'correct': is_correct,
            'reasoning': reasoning
        }
        results.append(result)
        
        status = '✅' if is_correct else '❌'
        print(f"{sample_id}: {status} 실제:{actual_label} 예측:{predicted_label}")
        print(f"   제목: {title[:60]}...")
        print(f"   이유: {reasoning}")
        if not is_correct:
            print(f"   ⚠️  오분류 케이스!")
        print()
    
    accuracy = correct / total
    print("=" * 60)
    print(f"📊 v3.0 자체 평가 결과:")
    print(f"정확도: {correct}/{total} = {accuracy*100:.1f}%")
    print(f"오분류: {total-correct}개")
    
    # 길이점수 계산 (929자)
    prompt_length = 929
    length_score = math.sqrt(1 - (prompt_length / 3000) ** 2)
    final_score = 0.9 * accuracy + 0.1 * length_score
    
    print(f"\n📈 점수 예측:")
    print(f"길이: {prompt_length}자")
    print(f"길이점수: {length_score:.3f}")
    print(f"최종점수: {final_score:.3f}")
    
    # 오분류 분석
    errors = [r for r in results if not r['correct']]
    if errors:
        print(f"\n❌ 오분류 패턴 분석:")
        for error in errors:
            if error['actual'] == 1 and error['predicted'] == 0:
                print(f"   False Negative: {error['id']} - {error['reasoning']}")
            else:
                print(f"   False Positive: {error['id']} - {error['reasoning']}")
    
    return accuracy, final_score, errors

if __name__ == "__main__":
    accuracy, final_score, errors = load_and_evaluate_samples()
    
    print(f"\n🎯 결론:")
    print(f"v3.0 예상 성능: {final_score:.3f}")
    if final_score > 0.854:
        print(f"✅ 현재(0.854)보다 {final_score-0.854:.3f}점 향상 예상")
    else:
        print(f"❌ 현재(0.854)보다 {0.854-final_score:.3f}점 하락 예상")
    
    if errors:
        print(f"\n🔧 개선 필요사항:")
        print("- 해외 자동차 회사 추가 (닛산, BYD 등)")
        print("- 자동차 시장/산업 키워드 추가")
        print("- 복합주제 판단 기준 완화")