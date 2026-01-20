#!/usr/bin/env python3
"""
v3.1 IMPROVED 프롬프트 완전 자체 평가
전체 샘플 대상 예측 정확도 측정
"""

import csv
import math
from typing import List, Dict, Tuple

def classify_with_v31_rules(title: str, content: str, sample_id: str) -> Tuple[int, str]:
    """v3.1 IMPROVED 규칙으로 분류"""
    text = (title + " " + content).lower()
    
    # v3.1 즉시1 회사명 (해외회사 추가)
    auto_companies = [
        "현대차", "현대자동차", "기아", "삼성sdi", "lg에너지솔루션", 
        "한온", "포티투", "채비", "한국타이어",
        "닛산", "혼다", "토요타", "테슬라", "byd", "bmw", "폭스바겐", "gm", "포드"
    ]
    
    # v3.1 즉시1 제품/기술/시장 키워드 (확장)
    auto_keywords = [
        "전기차", "ev", "suv", "하이브리드", "자율주행", "adas", 
        "완성차", "oem", "충전인프라", "자동차시장", "전기차시장", 
        "자동차산업", "완성차업계", "자동차업계", "차판매", "자동차연구원"
    ]
    
    # 즉시0 주제 (순수 비자동차)
    non_auto_topics = [
        "정치", "국방", "우주", "의료", "교육", "게임", "문화",
        "통신", "포털", "유통", "건설", "조선", "항공", "부동산", "금융"
    ]
    
    # 위험케이스 (무조건 0)
    risk_cases = [
        "uam", "항공", "선박", "우주", "가전배터리", "ess배터리", "산업용배터리",
        "서버반도체", "스마트폰반도체", "검색ai", "챗봇"
    ]
    
    # 위험케이스 체크
    for risk in risk_cases:
        if risk in text:
            return 0, f"위험케이스: {risk}"
    
    # 즉시0 주제 체크 (자동차 언급 없음)
    auto_mentioned = any(k in text for k in ["자동차", "전기차", "완성차", "자율주행"])
    for topic in non_auto_topics:
        if topic in text and not auto_mentioned:
            return 0, f"즉시0주제: {topic} (자동차 언급 없음)"
    
    # 즉시1 회사명 체크
    has_company = any(company in text for company in auto_companies)
    if has_company:
        return 1, f"즉시1: 자동차회사명"
    
    # 즉시1 키워드 체크
    has_keyword = any(keyword in text for keyword in auto_keywords)
    if has_keyword:
        return 1, f"즉시1: 자동차키워드"
    
    # 정부정책 특별규칙
    gov_keywords = ["정부", "정책", "지원", "투자"]
    auto_title_keywords = ["자동차", "전기차", "완성차", "자율주행"]
    
    has_gov = any(k in text for k in gov_keywords)
    has_auto_in_title = any(k in title.lower() for k in auto_title_keywords)
    
    if has_gov and has_auto_in_title:
        return 1, "정부정책: 제목에 자동차 명시"
    elif has_gov:
        return 0, "정부정책: 제목에 자동차 미명시"
    
    # 배터리/반도체 규칙
    if "배터리" in text:
        if any(x in text for x in ["전기차", "차량용", "ev"]) or has_company:
            return 1, "배터리: 전기차용/자동차회사"
        return 0, "배터리: 용도불명확"
    
    if "반도체" in text:
        if any(x in text for x in ["차량용", "자율주행"]) or has_company:
            return 1, "반도체: 차량용/자동차회사"
        return 0, "반도체: 용도불명확"
    
    # 기본값: 확신부족시 0
    return 0, "확신부족: 보수적접근"

def load_samples_from_csv():
    """CSV에서 전체 샘플 로드"""
    samples = []
    try:
        with open('data/samples.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                samples.append({
                    'id': row.get('id', ''),
                    'title': row.get('title', ''),
                    'content': row.get('content', ''),
                    'label': int(row.get('label', 0))
                })
    except Exception as e:
        print(f"CSV 로드 오류: {e}")
        return []
    
    return samples

def evaluate_v31_complete():
    """v3.1 전체 샘플 자체 평가"""
    print("🧪 v3.1 IMPROVED 완전 자체 평가")
    print("=" * 60)
    
    samples = load_samples_from_csv()
    if not samples:
        print("❌ 샘플 데이터를 로드할 수 없습니다.")
        return
    
    print(f"📊 총 {len(samples)}개 샘플 평가 시작...")
    
    results = []
    correct = 0
    total = 0
    false_positives = []
    false_negatives = []
    
    for sample in samples:
        predicted_label, reasoning = classify_with_v31_rules(
            sample['title'], sample['content'], sample['id']
        )
        
        actual_label = sample['label']
        is_correct = predicted_label == actual_label
        
        if is_correct:
            correct += 1
        else:
            if actual_label == 1 and predicted_label == 0:
                false_negatives.append({
                    'id': sample['id'],
                    'title': sample['title'][:60],
                    'reasoning': reasoning
                })
            else:
                false_positives.append({
                    'id': sample['id'], 
                    'title': sample['title'][:60],
                    'reasoning': reasoning
                })
        
        total += 1
        
        # 진행률 표시
        if total % 50 == 0:
            print(f"진행률: {total}/{len(samples)} ({total/len(samples)*100:.1f}%)")
    
    accuracy = correct / total
    
    print("\n" + "=" * 60)
    print(f"📊 v3.1 자체 평가 최종 결과:")
    print(f"정확도: {correct}/{total} = {accuracy*100:.1f}%")
    print(f"오분류: {total-correct}개 (FN: {len(false_negatives)}, FP: {len(false_positives)})")
    
    # 점수 계산
    prompt_length = 1057  # v3.1 길이
    length_score = math.sqrt(1 - (prompt_length / 3000) ** 2)
    final_score = 0.9 * accuracy + 0.1 * length_score
    
    print(f"\n📈 점수 예측:")
    print(f"길이: {prompt_length}자")
    print(f"길이점수: {length_score:.3f}")
    print(f"최종점수: {final_score:.3f}")
    print(f"vs 실전(0.854): {final_score-0.854:+.3f}")
    
    # 오분류 분석
    print(f"\n❌ False Negative 분석 (실제1→예측0):")
    for i, fn in enumerate(false_negatives[:10]):  # 상위 10개만
        print(f"  {i+1}. {fn['id']}: {fn['title']} - {fn['reasoning']}")
    if len(false_negatives) > 10:
        print(f"  ... 외 {len(false_negatives)-10}개")
    
    print(f"\n❌ False Positive 분석 (실제0→예측1):")
    for i, fp in enumerate(false_positives[:10]):  # 상위 10개만
        print(f"  {i+1}. {fp['id']}: {fp['title']} - {fp['reasoning']}")
    if len(false_positives) > 10:
        print(f"  ... 외 {len(false_positives)-10}개")
    
    return accuracy, final_score, len(false_negatives), len(false_positives)

if __name__ == "__main__":
    accuracy, final_score, fn_count, fp_count = evaluate_v31_complete()
    
    print(f"\n🎯 v3.1 성능 예측 결론:")
    print(f"예상 최종점수: {final_score:.3f}")
    
    if final_score > 0.854:
        improvement = final_score - 0.854
        print(f"✅ 현재(0.854)보다 {improvement:.3f}점 향상 예상")
        rank_estimate = max(1, int(250 * (0.854 / final_score)))
        print(f"🚀 예상 순위: ~{rank_estimate}등 (현재 250등 대비)")
    else:
        decline = 0.854 - final_score
        print(f"❌ 현재(0.854)보다 {decline:.3f}점 하락 예상")
    
    print(f"\n📊 오분류 패턴:")
    print(f"- False Negative: {fn_count}개 (놓친 자동차 뉴스)")
    print(f"- False Positive: {fp_count}개 (잘못 분류한 비자동차 뉴스)")