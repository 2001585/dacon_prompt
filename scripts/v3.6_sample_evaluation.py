#!/usr/bin/env python3
"""
v3.6 SAMPLE_VERIFIED 프롬프트로 전체 샘플 323개 자체 평가
"""

import csv
import math
from typing import List, Dict, Tuple

def classify_with_v36_rules(title: str, content: str, sample_id: str) -> Tuple[int, str]:
    """v3.6 규칙으로 분류"""
    text = (title + " " + content).lower()
    title_lower = title.lower()
    
    # v3.6 회사명
    companies = [
        "현대차", "현대자동차", "기아", "삼성sdi", "lg에너지솔루션", 
        "한온", "포티투", "채비", "한국타이어", "닛산", "혼다", "토요타", 
        "테슬라", "byd", "bmw", "폭스바겐", "gm", "포드"
    ]
    
    # v3.6 키워드
    keywords = [
        "전기차", "ev", "suv", "하이브리드", "수소차", "자율주행", "adas", 
        "완성차", "oem", "충전인프라", "자동차시장", "전기차시장", 
        "자동차산업", "완성차업계", "자동차업계", "차판매", "모빌리티", "자동차연구원"
    ]
    
    # 비자동차 분야
    non_auto = [
        "정치", "국방", "우주", "의료", "교육", "게임", "문화", 
        "통신", "포털", "유통", "건설", "조선", "항공", "부동산", "금융"
    ]
    
    # 위험 케이스 (무조건 0)
    danger = [
        "uam", "항공", "선박", "우주", "가전배터리", "ess배터리", 
        "서버반도체", "스마트폰반도체", "검색ai", "챗봇"
    ]
    
    # 위험케이스 체크
    for d in danger:
        if d in text:
            return 0, f"위험케이스: {d}"
    
    # 회사명이나 키워드 체크
    found_company = [c for c in companies if c in text]
    found_keyword = [k for k in keywords if k in text]
    
    if found_company or found_keyword:
        return 1, f"회사명/키워드: {found_company + found_keyword}"
    
    # 순수 비자동차 + 자동차 언급 없음 체크
    auto_mentions = any(x in text for x in ["자동차", "전기차", "완성차", "자율주행", "모빌리티"])
    non_auto_found = [n for n in non_auto if n in text]
    
    if non_auto_found and not auto_mentions:
        return 0, f"순수 비자동차: {non_auto_found}, 자동차 언급 없음"
    
    # 정부정책 특별규칙
    gov_keywords = ["정부", "정책", "지원", "투입"]
    auto_title_keywords = ["자동차", "전기차", "완성차", "자율주행", "모빌리티"]
    
    has_gov = any(k in text for k in gov_keywords)
    has_auto_in_title = any(k in title_lower for k in auto_title_keywords)
    
    if has_gov:
        if has_auto_in_title:
            return 1, "정부정책: 제목에 자동차 키워드 있음"
        else:
            return 0, "정부정책: 제목에 자동차 키워드 없음"
    
    # 배터리 특별규칙
    if "배터리" in text:
        battery_auto = ["전기차용", "차량용", "ev용"]
        if any(b in text for b in battery_auto) or found_company:
            return 1, "배터리: 전기차용/차량용 또는 자동차회사 언급"
        return 0, "배터리: 용도 불명확"
    
    # 확실하지 않으면 0
    return 0, "확실하지 않음"

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

def evaluate_v36_complete():
    """v3.6 전체 샘플 자체 평가"""
    print("🧪 v3.6 SAMPLE_VERIFIED 완전 자체 평가")
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
        predicted_label, reasoning = classify_with_v36_rules(
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
                    'title': sample['title'][:50],
                    'reasoning': reasoning
                })
            else:
                false_positives.append({
                    'id': sample['id'], 
                    'title': sample['title'][:50],
                    'reasoning': reasoning
                })
        
        total += 1
        
        # 진행률 표시
        if total % 50 == 0:
            print(f"진행률: {total}/{len(samples)} ({total/len(samples)*100:.1f}%)")
    
    accuracy = correct / total
    
    print("\n" + "=" * 60)
    print(f"📊 v3.6 자체 평가 최종 결과:")
    print(f"정확도: {correct}/{total} = {accuracy*100:.1f}%")
    print(f"오분류: {total-correct}개 (FN: {len(false_negatives)}, FP: {len(false_positives)})")
    
    # 점수 계산
    prompt_length = 1020  # v3.6 길이
    length_score = math.sqrt(1 - (prompt_length / 3000) ** 2)
    final_score = 0.9 * accuracy + 0.1 * length_score
    
    print(f"\n📈 점수 예측:")
    print(f"길이: {prompt_length}자")
    print(f"길이점수: {length_score:.3f}")
    print(f"최종점수: {final_score:.3f}")
    print(f"vs v3.3(0.837): {final_score-0.837:+.3f}")
    
    # 오분류 분석
    if false_negatives:
        print(f"\n❌ False Negative 분석 (실제1→예측0) - {len(false_negatives)}개:")
        for i, fn in enumerate(false_negatives[:10]):
            print(f"  {i+1}. {fn['id']}: {fn['title']} - {fn['reasoning']}")
        if len(false_negatives) > 10:
            print(f"  ... 외 {len(false_negatives)-10}개")
    
    if false_positives:
        print(f"\n❌ False Positive 분석 (실제0→예측1) - {len(false_positives)}개:")
        for i, fp in enumerate(false_positives[:10]):
            print(f"  {i+1}. {fp['id']}: {fp['title']} - {fp['reasoning']}")
        if len(false_positives) > 10:
            print(f"  ... 외 {len(false_positives)-10}개")
    
    return accuracy, final_score, len(false_negatives), len(false_positives)

if __name__ == "__main__":
    accuracy, final_score, fn_count, fp_count = evaluate_v36_complete()
    
    print(f"\n🎯 v3.6 성능 예측 결론:")
    print(f"자체평가 점수: {final_score:.3f}")
    
    if final_score > 0.837:
        improvement = final_score - 0.837
        print(f"✅ v3.3(0.837)보다 {improvement:.3f}점 향상 예상")
        print(f"🚀 실제 제출 권장!")
    else:
        decline = 0.837 - final_score
        print(f"❌ v3.3(0.837)보다 {decline:.3f}점 하락 예상")
        print(f"⚠️  재검토 필요")
    
    print(f"\n📊 오분류 패턴:")
    print(f"- False Negative: {fn_count}개 (놓친 자동차 뉴스)")
    print(f"- False Positive: {fp_count}개 (잘못 분류한 비자동차 뉴스)")
    
    if accuracy >= 0.90:
        print(f"\n🎉 자체평가 90%+ 달성! 실제 제출 강력 권장!")
    elif accuracy >= 0.85:
        print(f"\n✅ 자체평가 85%+ 달성! 제출 권장!")
    else:
        print(f"\n⚠️  자체평가 85% 미달, 추가 개선 필요")