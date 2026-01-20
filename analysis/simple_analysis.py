import csv
import re
from collections import Counter

def analyze_samples():
    print("DACON 자동차 뉴스 분류 - 간단 분석")
    print("=" * 50)
    
    # 데이터 로드
    data = []
    with open('data/samples.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['ID'] and row['label']:  # 유효한 행만
                data.append(row)
    
    print(f"전체 샘플 수: {len(data)}")
    
    # 라벨 분포 분석
    labels = [int(row['label']) for row in data if row['label'].isdigit()]
    label_0 = sum(1 for l in labels if l == 0)
    label_1 = sum(1 for l in labels if l == 1)
    
    print(f"\n=== 라벨 분포 ===")
    print(f"자동차 무관(0): {label_0}개 ({label_0/len(labels)*100:.1f}%)")
    print(f"자동차 관련(1): {label_1}개 ({label_1/len(labels)*100:.1f}%)")
    
    # 자동차 관련 키워드 분석
    auto_keywords = [
        '현대차', '현대자동차', '기아', '삼성SDI', '차량', '자동차', '전기차', 'EV', 
        '배터리', '현대', '기아자동차', 'BMW', '벤츠', '아우디', '폭스바겐', 
        '토요타', '닛산', '혼다', '테슬라', '포드', 'GM', '쌍용',
        '판매', '생산', '공장', '조립', '제조', '완성차', 'SUV', '세단',
        '하이브리드', '내연기관', '엔진', '모터', '충전', '주행', '연비',
        '자율주행', '운전', '타이어', '부품', 'LG에너지솔루션', 'SK이노베이션'
    ]
    
    # 라벨별 키워드 빈도 분석
    keyword_stats = {}
    
    for label in [0, 1]:
        label_texts = []
        for row in data:
            if row['label'] == str(label):
                text = row['title'] + ' ' + row['content']
                label_texts.append(text)
        
        keyword_counts = {}
        for keyword in auto_keywords:
            count = 0
            for text in label_texts:
                count += text.count(keyword)
            if count > 0:
                keyword_counts[keyword] = count
        
        keyword_stats[label] = keyword_counts
    
    print(f"\n=== 자동차 관련 키워드 분석 ===")
    print("자동차 관련(1) 뉴스에서 자주 나오는 키워드:")
    
    if 1 in keyword_stats:
        sorted_keywords = sorted(keyword_stats[1].items(), key=lambda x: x[1], reverse=True)
        for keyword, count in sorted_keywords[:15]:
            print(f"  {keyword}: {count}회")
    
    print("\n자동차 무관(0) 뉴스에서 나오는 자동차 키워드:")
    if 0 in keyword_stats:
        sorted_keywords = sorted(keyword_stats[0].items(), key=lambda x: x[1], reverse=True)
        for keyword, count in sorted_keywords[:10]:
            print(f"  {keyword}: {count}회")
    
    # 텍스트 길이 분석
    print(f"\n=== 텍스트 길이 분석 ===")
    
    title_lengths = {'0': [], '1': []}
    content_lengths = {'0': [], '1': []}
    
    for row in data:
        if row['label'] in ['0', '1']:
            title_lengths[row['label']].append(len(row['title']))
            content_lengths[row['label']].append(len(row['content']))
    
    for label in ['0', '1']:
        label_name = '자동차 무관' if label == '0' else '자동차 관련'
        print(f"\n{label_name}({label}) 뉴스:")
        
        if title_lengths[label]:
            avg_title = sum(title_lengths[label]) / len(title_lengths[label])
            print(f"  평균 제목 길이: {avg_title:.1f}자")
        
        if content_lengths[label]:
            avg_content = sum(content_lengths[label]) / len(content_lengths[label])
            print(f"  평균 내용 길이: {avg_content:.1f}자")
    
    # 샘플 확인
    print(f"\n=== 샘플 확인 ===")
    
    print("자동차 관련(1) 뉴스 제목 예시:")
    count = 0
    for row in data:
        if row['label'] == '1' and count < 3:
            print(f"  - {row['title']}")
            count += 1
    
    print("\n자동차 무관(0) 뉴스 제목 예시:")
    count = 0
    for row in data:
        if row['label'] == '0' and count < 3:
            print(f"  - {row['title']}")
            count += 1

if __name__ == "__main__":
    analyze_samples()
