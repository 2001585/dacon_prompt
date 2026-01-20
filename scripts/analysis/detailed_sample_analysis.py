"""
샘플별 상세 분석 - 어떤 샘플을 어떤 프롬프트가 맞췄는지
"""

import json
import pandas as pd
from typing import Dict, List

def load_results():
    """결과 파일 로드"""
    with open('results/local_llm_results_Llama-3.2-3B-Instruct-GGUF_20250915_165743.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_each_sample():
    """각 샘플별로 어떤 프롬프트가 맞췄는지 분석"""
    results = load_results()
    df = pd.read_csv('data/samples.csv')

    # 샘플별 분석
    sample_performance = {}

    for prompt_result in results:
        prompt_name = prompt_result['name']
        for i, sample in enumerate(prompt_result['detailed_results']):
            sample_id = sample['id']

            if sample_id not in sample_performance:
                sample_performance[sample_id] = {
                    'title': sample['title'],
                    'actual': sample['actual'],
                    'correct_prompts': [],
                    'wrong_prompts': [],
                    'predictions': {}
                }

            sample_performance[sample_id]['predictions'][prompt_name] = sample['predicted']

            if sample['correct']:
                sample_performance[sample_id]['correct_prompts'].append(prompt_name)
            else:
                sample_performance[sample_id]['wrong_prompts'].append(prompt_name)

    return sample_performance

def print_detailed_analysis():
    """상세 분석 출력"""
    sample_perf = analyze_each_sample()

    print("\n" + "="*80)
    print("샘플별 상세 분석")
    print("="*80)

    # 통계
    all_correct = []  # 모든 프롬프트가 맞춘 샘플
    all_wrong = []    # 모든 프롬프트가 틀린 샘플
    mixed = []        # 의견이 갈린 샘플

    for sample_id, data in sample_perf.items():
        correct_count = len(data['correct_prompts'])
        total_count = len(data['predictions'])

        if correct_count == total_count:
            all_correct.append(sample_id)
        elif correct_count == 0:
            all_wrong.append(sample_id)
        else:
            mixed.append(sample_id)

    print(f"\n[통계]")
    print(f"총 샘플: {len(sample_perf)}개")
    print(f"모든 프롬프트가 맞춘 샘플: {len(all_correct)}개")
    print(f"모든 프롬프트가 틀린 샘플: {len(all_wrong)}개")
    print(f"의견이 갈린 샘플: {len(mixed)}개")

    # 모든 프롬프트가 맞춘 샘플 (이것이 핵심!)
    print("\n" + "="*80)
    print("[핵심] 모든 프롬프트가 정답을 맞춘 샘플")
    print("="*80)
    if all_correct:
        for sample_id in all_correct:
            data = sample_perf[sample_id]
            print(f"  {sample_id}: {data['title'][:50]}... (정답={data['actual']})")
    else:
        print("  없음 - 모든 프롬프트가 완벽하게 맞춘 샘플이 없음!")

    # 모든 프롬프트가 틀린 샘플 (공통 약점)
    print("\n" + "="*80)
    print("[약점] 모든 프롬프트가 틀린 샘플")
    print("="*80)
    if all_wrong:
        for sample_id in all_wrong:
            data = sample_perf[sample_id]
            print(f"  {sample_id}: {data['title'][:50]}... (정답={data['actual']})")
            # 왜 틀렸는지 분석
            predictions = set(data['predictions'].values())
            print(f"    -> 모두 {predictions}로 예측 (정답은 {data['actual']})")
    else:
        print("  없음")

    # 프롬프트별 성능 비교
    print("\n" + "="*80)
    print("프롬프트별 성능")
    print("="*80)

    prompt_scores = {}
    for sample_id, data in sample_perf.items():
        for prompt_name in data['predictions']:
            if prompt_name not in prompt_scores:
                prompt_scores[prompt_name] = {'correct': 0, 'total': 0}

            prompt_scores[prompt_name]['total'] += 1
            if prompt_name in data['correct_prompts']:
                prompt_scores[prompt_name]['correct'] += 1

    for prompt_name, scores in prompt_scores.items():
        accuracy = scores['correct'] / scores['total']
        print(f"{prompt_name}: {scores['correct']}/{scores['total']} = {accuracy:.1%}")

    # 각 샘플별 상세 정보
    print("\n" + "="*80)
    print("각 샘플별 예측 결과")
    print("="*80)

    for sample_id, data in sorted(sample_perf.items()):
        print(f"\n{sample_id}: {data['title'][:60]}...")
        print(f"  정답: {data['actual']}")
        print(f"  예측 결과:")
        for prompt_name, prediction in data['predictions'].items():
            status = "O" if prediction == data['actual'] else "X"
            print(f"    [{status}] {prompt_name}: {prediction}")

def find_best_prompt_combination():
    """가장 많은 샘플을 맞춘 프롬프트 조합 찾기"""
    sample_perf = analyze_each_sample()

    print("\n" + "="*80)
    print("프롬프트 조합 분석")
    print("="*80)

    # 각 프롬프트가 맞춘 샘플 목록
    prompt_correct_samples = {}
    for sample_id, data in sample_perf.items():
        for prompt_name in data['correct_prompts']:
            if prompt_name not in prompt_correct_samples:
                prompt_correct_samples[prompt_name] = set()
            prompt_correct_samples[prompt_name].add(sample_id)

    # 프롬프트 조합으로 커버 가능한 샘플
    all_samples = set(sample_perf.keys())

    print("\n[개별 프롬프트 커버리지]")
    for prompt_name, correct_samples in prompt_correct_samples.items():
        print(f"{prompt_name}: {len(correct_samples)}개 샘플 정답")

    # 모든 프롬프트 조합시 커버 가능한 샘플
    all_covered = set()
    for samples in prompt_correct_samples.values():
        all_covered.update(samples)

    print(f"\n[전체 커버리지]")
    print(f"3개 프롬프트 중 하나라도 맞춘 샘플: {len(all_covered)}/{len(all_samples)}")
    print(f"아무도 못 맞춘 샘플: {len(all_samples - all_covered)}개")

    # 못 맞춘 샘플 분석
    never_correct = all_samples - all_covered
    if never_correct:
        print("\n[아무도 못 맞춘 샘플]")
        for sample_id in never_correct:
            data = sample_perf[sample_id]
            print(f"  {sample_id}: {data['title'][:50]}... (정답={data['actual']})")

if __name__ == "__main__":
    print_detailed_analysis()
    find_best_prompt_combination()
