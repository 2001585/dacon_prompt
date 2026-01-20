#!/usr/bin/env python3
"""
완전무결 데이터 분석 - 46개 샘플 전수 분석
GPT-4o mini | temperature: 0.4 기준 최적화
"""

import csv
import json
from datetime import datetime

# v1.3 규칙을 Python 함수로 변환
def classify_with_v13_rules(title, content):
    """v1.3 규칙으로 분류 (수동)"""
    text = (title + " " + content).lower()
    
    # T1급-확실한 자동차(→1)
    t1_companies = ["현대차", "기아", "삼성sdi", "lg이노텍", "lg에너지솔루션", "한온시스템", "포티투닷", "채비", "코오롱인더", "한국타이어", "넥센타이어"]
    t1_products = ["전기차", "ev", "suv", "세단", "하이브리드", "승용차", "상용차", "트럭", "버스"]
    t1_tech = ["자율주행", "adas", "완성차", "oem", "충전인프라", "급속충전", "차량용"]
    t1_parts = ["타이어", "모터", "엔진", "브레이크", "에어백"]
    
    # T3급-확실한 비자동차(→0)  
    t3_fields = ["부동산", "금융", "정치", "군사", "우주", "의료", "교육", "게임", "요리", "패션", "문화", "스포츠"]
    t3_industries = ["통신", "포털", "유통", "건설", "조선", "항공", "화학", "석유", "철강"]
    
    # T1 키워드 체크
    for keyword in t1_companies + t1_products + t1_tech + t1_parts:
        if keyword in text:
            return 1, f"T1키워드: {keyword}"
    
    # 배터리 맥락 판단
    if "배터리" in text:
        if any(x in text for x in ["전기차", "차량용", "ev", "자동차"]):
            return 1, "T2-배터리: 전기차용"
        elif any(x in text for x in ["가전", "ess", "태양광", "산업용"]):
            return 0, "T2-배터리: 비자동차용"
    
    # T3 키워드 체크
    for keyword in t3_fields + t3_industries:
        if keyword in text:
            return 0, f"T3키워드: {keyword}"
    
    # 트릭케이스 체크
    if "현대중공업" in text:
        return 0, "트릭케이스: 현대중공업≠현대차"
    if "기아대학교" in text:
        return 0, "트릭케이스: 기아대학교≠기아"
    
    # 불명확한 경우 보수적 0
    return 0, "불명확->보수적0"

def analyze_all_samples():
    """전체 샘플 분석"""
    print("🔍 완전무결 데이터 분석 시작")
    print("=" * 60)
    
    results = []
    correct = 0
    total = 0
    
    with open('data/samples.csv', 'r', encoding='utf-8') as file:
        # BOM 제거
        content = file.read()
        if content.startswith('\ufeff'):
            content = content[1:]
        
        lines = content.strip().split('\n')
        reader = csv.DictReader(lines)
        
        for row in reader:
            sample_id = row['ID']
            title = row['title']
            content_text = row['content']
            actual_label = int(row['label'])
            
            # v1.3 규칙으로 분류
            predicted_label, reasoning = classify_with_v13_rules(title, content_text)
            
            is_correct = predicted_label == actual_label
            if is_correct:
                correct += 1
            total += 1
            
            result = {
                'id': sample_id,
                'title': title[:100] + "..." if len(title) > 100 else title,
                'actual': actual_label,
                'predicted': predicted_label,
                'correct': is_correct,
                'reasoning': reasoning,
                'risk_level': 'LOW' if is_correct else 'HIGH'
            }
            results.append(result)
            
            status = '✅' if is_correct else '❌'
            print(f"{sample_id}: {status} 실제:{actual_label} 예측:{predicted_label} | {reasoning}")
            if not is_correct:
                print(f"   ⚠️ 제목: {title[:80]}...")
    
    print("\n" + "=" * 60)
    print(f"📊 분석 완료!")
    print(f"정확도: {correct}/{total} = {correct/total*100:.1f}%")
    print(f"오분류: {total-correct}개")
    
    # 오분류 케이스 상세 분석
    errors = [r for r in results if not r['correct']]
    if errors:
        print(f"\n❌ 오분류 케이스 {len(errors)}개:")
        for i, error in enumerate(errors, 1):
            print(f"{i}. {error['id']}: {error['title']}")
            print(f"   실제:{error['actual']} 예측:{error['predicted']} | {error['reasoning']}")
    
    # 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'results/complete_analysis_{timestamp}.json', 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_samples': total,
                'correct_predictions': correct,
                'accuracy': correct/total,
                'error_count': len(errors)
            },
            'detailed_results': results,
            'error_analysis': errors
        }, f, ensure_ascii=False, indent=2)
    
    return results, correct/total

def find_improvement_opportunities(results):
    """개선 기회 분석"""
    print("\n🔍 개선 기회 분석")
    print("=" * 40)
    
    errors = [r for r in results if not r['correct']]
    
    # 패턴 분석
    patterns = {}
    for error in errors:
        key = f"실제{error['actual']}→예측{error['predicted']}"
        if key not in patterns:
            patterns[key] = []
        patterns[key].append(error)
    
    for pattern, cases in patterns.items():
        print(f"\n📈 {pattern} 패턴: {len(cases)}개")
        for case in cases:
            print(f"  - {case['id']}: {case['title'][:60]}...")
            print(f"    이유: {case['reasoning']}")
    
    return patterns

if __name__ == "__main__":
    results, accuracy = analyze_all_samples()
    patterns = find_improvement_opportunities(results)
    
    print(f"\n🎯 현재 v1.3 성능: {accuracy*100:.1f}%")
    print("🚀 다음: 오분류 케이스 기반 슈퍼프롬프트 v2.0 설계!")
