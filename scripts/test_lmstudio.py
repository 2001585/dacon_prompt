#!/usr/bin/env python3
"""
DACON 자동차 뉴스 분류 테스트 스크립트 - LMStudio API 활용
v1.3 프롬프트 성능 검증
"""

import os
import csv
import json
import requests
import time
from datetime import datetime
from typing import List, Dict, Tuple
import math

# LMStudio API 설정
LMSTUDIO_API_KEY = "lm-studio"  # LMStudio 기본값
LMSTUDIO_ENDPOINT = "http://203.234.62.45:1234/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-20b"

# v1.3 최종 시스템 프롬프트
SYSTEM_PROMPT = """뉴스 자동차 관련 분류 전문가. 출력: 관련(1), 무관(0)만.

**T1급-확실한 자동차(→1)**
회사: 현대차,기아,삼성SDI,LG이노텍,LG에너지솔루션,한온시스템,포티투닷,채비,코오롱인더,한국타이어,넥센타이어
제품: 전기차,EV,SUV,세단,하이브리드,승용차,상용차,트럭,버스
기술: 자율주행,ADAS,완성차,OEM,충전인프라,급속충전,차량용
부품: 타이어,배터리(전기차용),모터,엔진,브레이크,에어백

**T3급-확실한 비자동차(→0)**
분야: 부동산,금융,정치,군사,우주,의료,교육,게임,요리,패션,문화,스포츠
업종: 통신,포털,유통,건설,조선,항공,화학,석유,철강

**T2급-맥락판단 필수**
A)배터리: 전기차/차량용/EV→1, 가전/ESS/태양광/산업용→0
B)반도체: 차량용/자율주행/ADAS→1, 서버/스마트폰/PC/메모리→0  
C)AI/로봇: 자율주행AI/차량AI→1, 검색AI/챗봇/게임AI/의료AI→0
D)디스플레이: 차량용/대시보드/HUD→1, TV/스마트폰/PC/가전→0
E)소재/부품: 자동차소재/차량부품/완성차납품→1, 건설/가전/일반산업→0

**트릭케이스**
현대차≠현대중공업,기아≠기아대학교,삼성전자≠삼성SDI,LG전자≠LG이노텍

**판단단계**
1.T1키워드→즉시1
2.T3키워드→즉시0
3.T2맥락분석: 제목"자동차/차량용/완성차"명시→1, "가전/산업용/일반"명시→0, 본문 자동차회사고객→1, 본문 비자동차용도→0
4.불명확→보수적0

**핵심예시**
"삼성SDI 전기차배터리공장"→1(T1:삼성SDI+전기차)
"삼성SDI 가전용배터리"→0(가전용=비자동차)
"LG화학 자동차소재개발"→1(자동차소재=자동차용)
"현대중공업 선박엔진"→0(현대중공업≠현대차)
"AI 자율주행기술"→1(자율주행=자동차)
"SK하이닉스 차량용반도체"→1(차량용=자동차)
"포스코 자동차향 철강"→1(자동차향=자동차용)
"네이버 AI검색"→0(검색AI=비자동차)

**복합주제처리**
정치+자동차: "정부 자동차지원정책"→주제비중판단→자동차정책 중심→1
경제+자동차: "자동차업계 수출현황"→자동차업계 중심→1
기술+자동차: "반도체 자율주행적용"→자율주행=자동차→1

반드시 0또는1만 출력."""

class LMStudioTester:
    def __init__(self):
        self.api_key = LMSTUDIO_API_KEY
        self.endpoint = LMSTUDIO_ENDPOINT
        self.results = []
        self.test_start_time = None
        
    def test_connection(self) -> bool:
        """LMStudio 서버 연결 테스트"""
        try:
            response = requests.post(
                self.endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": "테스트"}],
                    "max_tokens": 1,
                    "temperature": 0
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ LMStudio 서버 연결 성공")
                return True
            else:
                print(f"❌ LMStudio 서버 연결 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 연결 테스트 실패: {str(e)}")
            return False
    
    def classify_news(self, title: str, content: str) -> Tuple[str, str]:
        """뉴스 분류 실행"""
        user_message = f"제목: {title}\n내용: {content}"
        
        try:
            response = requests.post(
                self.endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    "max_tokens": 5,
                    "temperature": 0,
                    "stop": ["\n", " "]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_output = result["choices"][0]["message"]["content"].strip()
                
                # 0 또는 1 추출
                if "1" in raw_output:
                    classification = "1"
                elif "0" in raw_output:
                    classification = "0"
                else:
                    classification = "0"  # 보수적 접근
                    
                return classification, raw_output
            else:
                print(f"API 요청 실패: {response.status_code}")
                return "0", "ERROR"
                
        except Exception as e:
            print(f"분류 실패: {str(e)}")
            return "0", "ERROR"
    
    def load_samples(self, csv_path: str) -> List[Dict]:
        """data/samples.csv 로드"""
        samples = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    samples.append({
                        'id': row['id'],
                        'title': row['title'],
                        'content': row['content'],
                        'label': int(row['label'])
                    })
            print(f"✅ {len(samples)}개 샘플 로드 완료")
            return samples
        except Exception as e:
            print(f"❌ CSV 로드 실패: {str(e)}")
            return []
    
    def run_test(self, samples: List[Dict]) -> Dict:
        """전체 테스트 실행"""
        print(f"\n🚀 테스트 시작: {len(samples)}개 샘플")
        print("=" * 60)
        
        self.test_start_time = datetime.now()
        correct = 0
        total = 0
        
        for i, sample in enumerate(samples):
            print(f"\n[{i+1:2d}/{len(samples)}] {sample['id']}")
            print(f"제목: {sample['title'][:50]}...")
            print(f"실제 라벨: {sample['label']}")
            
            # 분류 실행
            predicted, raw_output = self.classify_news(sample['title'], sample['content'])
            predicted_int = int(predicted) if predicted in ['0', '1'] else 0
            
            # 결과 기록
            is_correct = predicted_int == sample['label']
            if is_correct:
                correct += 1
            total += 1
            
            result = {
                'id': sample['id'],
                'title': sample['title'],
                'content': sample['content'],
                'actual': sample['label'],
                'predicted': predicted_int,
                'raw_output': raw_output,
                'correct': is_correct,
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            
            print(f"예측: {predicted_int} | 원본출력: '{raw_output}' | {'✅ 정답' if is_correct else '❌ 오답'}")
            print(f"현재 정확도: {correct}/{total} = {correct/total*100:.1f}%")
            
            time.sleep(0.5)  # API 부하 방지
        
        # 최종 통계
        test_duration = datetime.now() - self.test_start_time
        accuracy = correct / total
        
        # 길이 점수 계산 (프롬프트 1976자 기준)
        prompt_length = len(SYSTEM_PROMPT)
        length_score = math.sqrt(1 - (prompt_length / 3000) ** 2)
        
        # 최종 점수 계산
        final_score = 0.9 * accuracy + 0.1 * length_score
        
        stats = {
            'total_samples': total,
            'correct_predictions': correct,
            'accuracy': accuracy,
            'prompt_length': prompt_length,
            'length_score': length_score,
            'final_score': final_score,
            'test_duration': str(test_duration),
            'target_score': 0.935
        }
        
        return stats
    
    def analyze_errors(self) -> Dict:
        """오분류 케이스 분석"""
        errors = [r for r in self.results if not r['correct']]
        
        print(f"\n📊 오분류 분석: {len(errors)}개")
        print("=" * 60)
        
        error_analysis = {
            'false_positives': [],  # 0인데 1로 예측
            'false_negatives': [],  # 1인데 0으로 예측
            'total_errors': len(errors)
        }
        
        for error in errors:
            print(f"\n❌ {error['id']}")
            print(f"제목: {error['title']}")
            print(f"실제: {error['actual']} | 예측: {error['predicted']}")
            print(f"원본 출력: '{error['raw_output']}'")
            
            if error['actual'] == 0 and error['predicted'] == 1:
                error_analysis['false_positives'].append(error)
                print("유형: False Positive (비자동차를 자동차로 오분류)")
            else:
                error_analysis['false_negatives'].append(error)
                print("유형: False Negative (자동차를 비자동차로 오분류)")
        
        return error_analysis
    
    def save_results(self, stats: Dict, error_analysis: Dict):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 상세 결과 저장
        with open(f'results/test_results_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump({
                'statistics': stats,
                'error_analysis': {
                    'false_positives': len(error_analysis['false_positives']),
                    'false_negatives': len(error_analysis['false_negatives']),
                    'total_errors': error_analysis['total_errors']
                },
                'detailed_results': self.results
            }, f, ensure_ascii=False, indent=2)
        
        # 요약 리포트 저장
        report = f"""# DACON 자동차 뉴스 분류 테스트 결과

## 📊 성능 통계
- **테스트 샘플**: {stats['total_samples']}개
- **정답 수**: {stats['correct_predictions']}개
- **정확도**: {stats['accuracy']:.1%} ({stats['accuracy']:.4f})
- **프롬프트 길이**: {stats['prompt_length']}자
- **길이 점수**: {stats['length_score']:.4f}
- **최종 점수**: {stats['final_score']:.4f}
- **목표 점수**: {stats['target_score']:.3f}
- **목표 달성**: {'✅ 달성' if stats['final_score'] >= stats['target_score'] else '❌ 미달성'}

## ❌ 오분류 분석
- **총 오분류**: {error_analysis['total_errors']}개
- **False Positive**: {len(error_analysis['false_positives'])}개 (비자동차→자동차)
- **False Negative**: {len(error_analysis['false_negatives'])}개 (자동차→비자동차)

## 🕒 테스트 정보
- **소요 시간**: {stats['test_duration']}
- **테스트 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(f'results/test_report_{timestamp}.md', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n💾 결과 저장 완료:")
        print(f"- results/test_results_{timestamp}.json")
        print(f"- results/test_report_{timestamp}.md")

def main():
    """메인 실행 함수"""
    print("🎯 DACON 자동차 뉴스 분류 테스트 - LMStudio")
    print("=" * 60)
    
    # 테스터 초기화
    tester = LMStudioTester()
    
    # 연결 테스트
    if not tester.test_connection():
        print("\n❌ LMStudio 서버에 연결할 수 없습니다.")
        print("1. LMStudio가 실행 중인지 확인하세요")
        print("2. 로컬 서버가 시작되었는지 확인하세요 (포트 1234)")
        print("3. 모델이 로드되었는지 확인하세요")
        return
    
    # 샘플 데이터 로드
    samples = tester.load_samples('data/samples.csv')
    if not samples:
        print("\n❌ 샘플 데이터를 로드할 수 없습니다.")
        print("data/samples.csv 파일을 확인하세요.")
        return
    
    # 테스트 실행
    stats = tester.run_test(samples)
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("🎉 테스트 완료!")
    print("=" * 60)
    print(f"정확도: {stats['accuracy']:.1%}")
    print(f"최종 점수: {stats['final_score']:.4f}")
    print(f"목표 달성: {'✅' if stats['final_score'] >= stats['target_score'] else '❌'}")
    
    # 오분류 분석
    error_analysis = tester.analyze_errors()
    
    # 결과 저장
    tester.save_results(stats, error_analysis)
    
if __name__ == "__main__":
    main()
