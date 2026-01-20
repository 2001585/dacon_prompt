"""
평가 결과 분석 도구
각 샘플별로 어떤 프롬프트가 성공/실패했는지 분석
"""

import json
import pandas as pd
from typing import Dict, List
import glob

def load_latest_results() -> List[Dict]:
    """가장 최근 결과 파일 로드"""
    result_files = glob.glob("results/local_llm_results_*.json")
    if not result_files:
        print("결과 파일이 없습니다.")
        return []

    latest_file = sorted(result_files)[-1]
    print(f"로드 중: {latest_file}")

    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_sample_performance(results: List[Dict]) -> pd.DataFrame:
    """각 샘플별 성능 분석"""
    # 샘플별 결과 수집
    sample_analysis = {}

    for prompt_result in results:
        prompt_name = prompt_result['name']
        for sample in prompt_result['detailed_results']:
            sample_id = sample['id']

            if sample_id not in sample_analysis:
                sample_analysis[sample_id] = {
                    'id': sample_id,
                    'title': sample['title'],
                    'actual': sample['actual'],
                    'prompts_correct': [],
                    'prompts_wrong': [],
                    'all_correct': True,
                    'all_wrong': True
                }

            if sample['correct']:
                sample_analysis[sample_id]['prompts_correct'].append(prompt_name)
                sample_analysis[sample_id]['all_wrong'] = False
            else:
                sample_analysis[sample_id]['prompts_wrong'].append(prompt_name)
                sample_analysis[sample_id]['all_correct'] = False

    # DataFrame으로 변환
    df = pd.DataFrame.from_dict(sample_analysis, orient='index')
    df['success_rate'] = df['prompts_correct'].apply(len) / len(results)

    return df.sort_values('id')

def print_analysis_report(df: pd.DataFrame, results: List[Dict]):
    """분석 보고서 출력"""
    print("\n" + "=" * 80)
    print("샘플별 상세 분석 보고서")
    print("=" * 80)

    # 전체 통계
    print("\n[전체 통계]:")
    print(f"  - 총 샘플 수: {len(df)}")
    print(f"  - 테스트한 프롬프트 수: {len(results)}")

    # 모든 프롬프트가 맞춘 샘플
    all_correct_samples = df[df['all_correct']]
    print(f"\nO 모든 프롬프트가 맞춘 샘플: {len(all_correct_samples)}개")
    if len(all_correct_samples) > 0:
        for _, row in all_correct_samples.iterrows():
            print(f"  - Sample {row['id']:2} (정답={row['actual']}): {row['title'][:50]}...")

    # 모든 프롬프트가 틀린 샘플
    all_wrong_samples = df[df['all_wrong']]
    print(f"\nX 모든 프롬프트가 틀린 샘플: {len(all_wrong_samples)}개")
    if len(all_wrong_samples) > 0:
        for _, row in all_wrong_samples.iterrows():
            print(f"  - Sample {row['id']:2} (정답={row['actual']}): {row['title'][:50]}...")

    # 성공률별 분석
    print("\n[성공률] 샘플별 성공률 분포:")
    success_rate_dist = df['success_rate'].value_counts().sort_index()
    for rate, count in success_rate_dist.items():
        bar = "=" * int(count * 2)
        print(f"  {rate:4.0%}: {bar} ({count}개)")

    # 각 샘플별 상세 결과
    print("\n[상세] 각 샘플별 상세 결과:")
    print("-" * 80)

    for _, row in df.iterrows():
        status = "O" if row['all_correct'] else ("X" if row['all_wrong'] else "?")
        print(f"\n[{status}] Sample {row['id']:2} - 정답: {row['actual']}")
        print(f"    제목: {row['title']}")
        print(f"    성공률: {row['success_rate']:.0%} ({len(row['prompts_correct'])}/{len(results)})")

        if row['prompts_correct']:
            print(f"    맞춘 프롬프트: {', '.join(row['prompts_correct'])}")
        if row['prompts_wrong']:
            print(f"    틀린 프롬프트: {', '.join(row['prompts_wrong'])}")

    # 프롬프트별 성능 요약
    print("\n" + "=" * 80)
    print("프롬프트별 성능 요약")
    print("=" * 80)

    for prompt_result in results:
        print(f"\n{prompt_result['name']}:")
        print(f"  - 정확도: {prompt_result['accuracy']:.2%} ({prompt_result['correct']}/{prompt_result['total']})")
        print(f"  - 예상 점수: {prompt_result['dacon_score']:.4f}")
        print(f"  - 길이: {prompt_result['length']}자")

def save_sample_analysis_csv(df: pd.DataFrame, filename: str = "data/sample_analysis.csv"):
    """샘플 분석 결과를 CSV로 저장"""
    # 리스트 컬럼을 문자열로 변환
    df_export = df.copy()
    df_export['prompts_correct'] = df_export['prompts_correct'].apply(lambda x: ', '.join(x))
    df_export['prompts_wrong'] = df_export['prompts_wrong'].apply(lambda x: ', '.join(x))

    df_export.to_csv(filename, encoding='utf-8-sig')
    print(f"\n[저장] 샘플 분석 결과 저장: {filename}")

def main():
    """메인 실행"""
    # 최신 결과 로드
    results = load_latest_results()
    if not results:
        return

    # 샘플별 성능 분석
    df = analyze_sample_performance(results)

    # 보고서 출력
    print_analysis_report(df, results)

    # CSV 저장
    save_sample_analysis_csv(df)

    # 문제 샘플 집중 분석
    print("\n" + "=" * 80)
    print("[집중분석] 문제 샘플 집중 분석 (성공률 50% 이하)")
    print("=" * 80)

    problem_samples = df[df['success_rate'] <= 0.5].sort_values('success_rate')
    if len(problem_samples) > 0:
        for _, row in problem_samples.iterrows():
            print(f"\nSample {row['id']} (성공률: {row['success_rate']:.0%})")
            print(f"  제목: {row['title']}")
            print(f"  정답: {row['actual']}")
            print(f"  분석: 이 샘플은 특별한 주의가 필요합니다.")

            # 원본 데이터에서 더 자세한 정보 찾기
            df_samples = pd.read_csv('data/samples.csv')
            sample_detail = df_samples[df_samples['id'] == row['id']].iloc[0]
            print(f"  본문 일부: {sample_detail['content'][:100]}...")

if __name__ == "__main__":
    main()
