import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
import numpy as np

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def load_and_analyze_data():
    """CSV 파일을 로드하고 기본 분석 수행"""
    # 데이터 로드
    df = pd.read_csv('data/samples.csv', encoding='utf-8-sig')
    
    print("=== 데이터 기본 정보 ===")
    print(f"전체 샘플 수: {len(df)}")
    print(f"컬럼: {list(df.columns)}")
    print("\n=== 결측값 확인 ===")
    print(df.isnull().sum())
    
    # 라벨 분포 확인
    print("\n=== 라벨 분포 ===")
    label_counts = df['label'].value_counts().sort_index()
    print(label_counts)
    print(f"자동차 관련(1): {label_counts[1]}/{len(df)} ({label_counts[1]/len(df)*100:.1f}%)")
    print(f"자동차 무관(0): {label_counts[0]}/{len(df)} ({label_counts[0]/len(df)*100:.1f}%)")
    
    # 시각화
    plt.figure(figsize=(12, 5))
    
    # 라벨 분포 바차트
    plt.subplot(1, 2, 1)
    label_counts.plot(kind='bar', color=['skyblue', 'lightcoral'])
    plt.title('자동차 관련 뉴스 분포')
    plt.xlabel('라벨 (0: 무관, 1: 관련)')
    plt.ylabel('개수')
    plt.xticks(rotation=0)
    
    # 파이차트
    plt.subplot(1, 2, 2)
    plt.pie(label_counts.values, labels=['자동차 무관(0)', '자동차 관련(1)'], 
            autopct='%1.1f%%', colors=['skyblue', 'lightcoral'])
    plt.title('자동차 관련 뉴스 비율')
    
    plt.tight_layout()
    plt.savefig('label_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return df

def analyze_text_features(df):
    """텍스트 특징 분석"""
    print("\n=== 텍스트 길이 분석 ===")
    
    # 제목 길이 분석
    df['title_length'] = df['title'].str.len()
    # 내용 길이 분석
    df['content_length'] = df['content'].str.len()
    
    print("제목 길이 통계:")
    print(df.groupby('label')['title_length'].describe())
    
    print("\n내용 길이 통계:")
    print(df.groupby('label')['content_length'].describe())
    
    # 시각화
    plt.figure(figsize=(15, 5))
    
    # 제목 길이 분포
    plt.subplot(1, 3, 1)
    for label in [0, 1]:
        data = df[df['label'] == label]['title_length']
        plt.hist(data, alpha=0.7, bins=20, 
                label=f'라벨 {label} (자동차 {"관련" if label == 1 else "무관"})')
    plt.xlabel('제목 길이 (문자 수)')
    plt.ylabel('빈도')
    plt.title('제목 길이 분포')
    plt.legend()
    
    # 내용 길이 분포
    plt.subplot(1, 3, 2)
    for label in [0, 1]:
        data = df[df['label'] == label]['content_length']
        plt.hist(data, alpha=0.7, bins=20, 
                label=f'라벨 {label} (자동차 {"관련" if label == 1 else "무관"})')
    plt.xlabel('내용 길이 (문자 수)')
    plt.ylabel('빈도')
    plt.title('내용 길이 분포')
    plt.legend()
    
    # 박스플롯
    plt.subplot(1, 3, 3)
    box_data = [df[df['label'] == 0]['content_length'], 
                df[df['label'] == 1]['content_length']]
    plt.boxplot(box_data, labels=['자동차 무관(0)', '자동차 관련(1)'])
    plt.ylabel('내용 길이 (문자 수)')
    plt.title('내용 길이 박스플롯')
    
    plt.tight_layout()
    plt.savefig('text_length_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return df

def extract_keywords(df):
    """자동차 관련 키워드 추출 및 분석"""
    print("\n=== 키워드 분석 ===")
    
    # 자동차 관련 기본 키워드들
    auto_keywords = [
        '현대차', '기아', '삼성', '차량', '자동차', '전기차', 'EV', '배터리',
        '현대자동차', '현대', '기아자동차', '쌍용', '르노', 'BMW', '벤츠', 
        '아우디', '폭스바겐', '토요타', '닛산', '혼다', '테슬라', '포드',
        '출시', '판매', '생산', '공장', '조립', '제조', '완성차', 'SUV',
        '세단', '하이브리드', '내연기관', '엔진', '모터', '충전', '주행',
        '연비', '안전', '자율주행', '운전', '도로', '교통', '타이어',
        '부품', '소재', '반도체', 'LG에너지솔루션', 'SK이노베이션', 'CATL'
    ]
    
    # 각 라벨별로 키워드 빈도 계산
    auto_related_keywords = []
    non_auto_related_keywords = []
    
    for idx, row in df.iterrows():
        text = row['title'] + ' ' + row['content']
        text = text.lower()
        
        found_keywords = []
        for keyword in auto_keywords:
            if keyword.lower() in text:
                found_keywords.append(keyword)
        
        if row['label'] == 1:
            auto_related_keywords.extend(found_keywords)
        else:
            non_auto_related_keywords.extend(found_keywords)
    
    # 키워드 빈도 분석
    auto_counter = Counter(auto_related_keywords)
    non_auto_counter = Counter(non_auto_related_keywords)
    
    print("자동차 관련 뉴스(1)에서 자주 나오는 키워드 TOP 10:")
    for keyword, count in auto_counter.most_common(10):
        print(f"  {keyword}: {count}회")
    
    print("\n자동차 무관 뉴스(0)에서 나오는 자동차 관련 키워드:")
    for keyword, count in non_auto_counter.most_common(5):
        print(f"  {keyword}: {count}회")
    
    return auto_counter, non_auto_counter

def analyze_specific_patterns(df):
    """특정 패턴 분석"""
    print("\n=== 특정 패턴 분석 ===")
    
    patterns = {
        '회사명_차': r'[가-힣]+차(?!\w)',  # 현대차, 기아차 등
        '전기_배터리': r'전기|배터리|EV|하이브리드',
        '자동차_산업': r'자동차|완성차|부품|조립',
        '생산_판매': r'생산|판매|출시|공장',
        '기술_관련': r'기술|개발|R&D|연구',
        '숫자_대': r'\d+[만천백십]?\s*대(?!\w)',  # 숫자 + 대
        '브랜드명': r'현대|기아|삼성|LG|SK|BMW|벤츠|아우디|테슬라'
    }
    
    results = {}
    
    for pattern_name, pattern in patterns.items():
        results[pattern_name] = {}
        for label in [0, 1]:
            texts = df[df['label'] == label]['title'] + ' ' + df[df['label'] == label]['content']
            matches = []
            for text in texts:
                matches.extend(re.findall(pattern, text))
            results[pattern_name][label] = len(matches)
    
    # 결과 출력
    for pattern_name, counts in results.items():
        total = counts[0] + counts[1]
        if total > 0:
            ratio_1 = counts[1] / total * 100
            print(f"{pattern_name}: 전체 {total}개 중 라벨1에서 {counts[1]}개 ({ratio_1:.1f}%)")
    
    return results

if __name__ == "__main__":
    print("DACON 자동차 뉴스 분류 - 기본 데이터 분석")
    print("=" * 50)
    
    # 데이터 로드 및 기본 분석
    df = load_and_analyze_data()
    
    # 텍스트 특징 분석
    df = analyze_text_features(df)
    
    # 키워드 분석
    auto_counter, non_auto_counter = extract_keywords(df)
    
    # 패턴 분석
    pattern_results = analyze_specific_patterns(df)
    
    print("\n분석 완료! 그래프 파일이 저장되었습니다.")
    print("- label_distribution.png: 라벨 분포")
    print("- text_length_analysis.png: 텍스트 길이 분석")
