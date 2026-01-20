import pandas as pd
import json
import re
from typing import Dict, List, Tuple
from datetime import datetime

# 평가 규칙 JSON
EVALUATION_RULES = {
    "automotive_keywords": {
        "strong_positive": {
            "keywords": ["현대차", "기아", "테슬라", "BMW", "도요타", "GM", "포드", "BYD", "닛산", "혼다",
                        "전기차", "하이브리드", "자율주행", "차량용 배터리", "차량용 반도체",
                        "충전소", "타이어", "OEM", "신차"],
            "weight": 3,
            "description": "자동차 제조사 및 핵심 기술"
        },
        "moderate_positive": {
            "keywords": ["EV", "HEV", "PHEV", "FCV", "자동차", "차량", "차종", "IVI", "ADAS",
                        "E-GMP", "PPE", "SSP", "NACS", "CCS", "AEC-Q", "ISO26262", "NCAP"],
            "weight": 2,
            "description": "자동차 관련 기술 용어"
        },
        "action_keywords": {
            "keywords": ["출시", "양산", "증설", "생산", "투자", "수주", "공급계약", "판매",
                        "수출입", "실적", "리콜", "인증"],
            "weight": 2,
            "description": "자동차 산업 행위"
        },
        "negative_keywords": {
            "keywords": ["ESS", "태양광", "가정용", "UAM", "항공", "조선", "정책", "무역",
                        "일반 배터리", "스마트폰", "로봇"],
            "weight": -3,
            "description": "비자동차 산업"
        }
    },
    "critical_patterns": {
        "vehicle_specific": {
            "pattern": r"차량용|자동차용|오토모티브|for EV|for vehicle",
            "importance": "HIGH",
            "description": "차량 전용 명시"
        },
        "manufacturer_action": {
            "pattern": r"(현대차|기아|테슬라|BMW).*(출시|생산|판매|투자)",
            "importance": "HIGH",
            "description": "제조사와 행위 동시 출현"
        }
    },
    "scoring_threshold": {
        "minimum_score": 3,
        "confidence_levels": {
            "high": 5,
            "medium": 3,
            "low": 1
        }
    }
}

class PromptEvaluator:
    def __init__(self, prompt_text: str, prompt_name: str):
        self.prompt = prompt_text
        self.name = prompt_name
        self.results = {
            "name": prompt_name,
            "length": len(prompt_text),
            "test_results": [],
            "accuracy": 0,
            "final_score": 0,
            "detailed_analysis": {}
        }

    def evaluate_single_case(self, title: str, content: str, actual_label: int) -> Dict:
        """단일 테스트 케이스 평가"""
        text = f"{title} {content}".lower()

        # 점수 계산
        score = 0
        matched_rules = []

        # 키워드 기반 스코어링
        for category, rules in EVALUATION_RULES["automotive_keywords"].items():
            for keyword in rules["keywords"]:
                if keyword.lower() in text:
                    score += rules["weight"]
                    matched_rules.append({
                        "category": category,
                        "keyword": keyword,
                        "weight": rules["weight"]
                    })

        # 패턴 매칭
        critical_match = False
        for pattern_name, pattern_info in EVALUATION_RULES["critical_patterns"].items():
            if re.search(pattern_info["pattern"], text, re.IGNORECASE):
                critical_match = True
                matched_rules.append({
                    "pattern": pattern_name,
                    "importance": pattern_info["importance"]
                })

        # 최종 판정
        if critical_match:
            predicted = 1 if score >= 1 else 0
        else:
            predicted = 1 if score >= EVALUATION_RULES["scoring_threshold"]["minimum_score"] else 0

        # 평가 결과
        is_correct = predicted == actual_label

        return {
            "title": title[:50] + "..." if len(title) > 50 else title,
            "actual": actual_label,
            "predicted": predicted,
            "score": score,
            "is_correct": is_correct,
            "matched_rules": matched_rules,
            "confidence": self._get_confidence(score)
        }

    def _get_confidence(self, score: int) -> str:
        """신뢰도 레벨 결정"""
        levels = EVALUATION_RULES["scoring_threshold"]["confidence_levels"]
        if abs(score) >= levels["high"]:
            return "HIGH"
        elif abs(score) >= levels["medium"]:
            return "MEDIUM"
        else:
            return "LOW"

    def run_evaluation(self, df: pd.DataFrame) -> Dict:
        """전체 평가 실행"""
        print(f"\n{'='*60}")
        print(f"평가 시작: {self.name}")
        print(f"프롬프트 길이: {self.results['length']}자")
        print(f"{'='*60}\n")

        correct_count = 0
        wrong_cases = []

        for idx, row in df.iterrows():
            result = self.evaluate_single_case(
                row['Title'],
                row['Content'],
                row['Label']
            )

            self.results["test_results"].append(result)

            # 콘솔 출력
            status = "✅ PASS" if result["is_correct"] else "❌ FAIL"
            confidence = result["confidence"]

            print(f"[{idx:02d}] {status} | 실제: {result['actual']} | 예측: {result['predicted']} | "
                  f"점수: {result['score']:+3d} | 신뢰도: {confidence:6s} | {result['title']}")

            if result["is_correct"]:
                correct_count += 1
            else:
                wrong_cases.append({
                    "index": idx,
                    "title": result["title"],
                    "actual": result["actual"],
                    "predicted": result["predicted"],
                    "score": result["score"]
                })

        # 정확도 계산
        self.results["accuracy"] = correct_count / len(df)

        # 데이콘 점수 계산
        length_score = max(0, 1 - (self.results["length"] - 300) / 2700) if self.results["length"] > 300 else 1
        self.results["final_score"] = 0.9 * self.results["accuracy"] + 0.1 * length_score

        # 상세 분석
        self.results["detailed_analysis"] = {
            "total_cases": len(df),
            "correct": correct_count,
            "wrong": len(wrong_cases),
            "wrong_cases": wrong_cases,
            "length_score": length_score
        }

        return self.results

    def print_summary(self):
        """평가 요약 출력"""
        print(f"\n{'='*60}")
        print(f"평가 완료: {self.name}")
        print(f"{'='*60}")
        print(f"정확도: {self.results['accuracy']:.4f} "
              f"({self.results['detailed_analysis']['correct']}/{self.results['detailed_analysis']['total_cases']})")
        print(f"길이: {self.results['length']}자")
        print(f"길이 점수: {self.results['detailed_analysis']['length_score']:.4f}")
        print(f"최종 점수: {self.results['final_score']:.4f}")

        if self.results['detailed_analysis']['wrong_cases']:
            print(f"\n틀린 케이스 ({len(self.results['detailed_analysis']['wrong_cases'])}개):")
            for case in self.results['detailed_analysis']['wrong_cases'][:5]:  # 처음 5개만
                print(f"  - [{case['index']}] {case['title']}")
                print(f"    실제: {case['actual']}, 예측: {case['predicted']}, 점수: {case['score']}")

    def save_json_report(self, filename: str):
        """JSON 리포트 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n📄 JSON 리포트 저장: {filename}")

def main():
    # 프롬프트 정의
    PROMPTS = {
        "Lv1_보수적_560자": """[역할] 뉴스클리핑 AI: 입력 기사 1건이 자동차와 직접 관련인지 분류.
[출력] "1" 또는 "0"만.
[집합]
A=완성차·OEM·전장·부품·타이어·충전·차량용EV배터리
Act=출시·양산·증설·생산·투자·수주·공급계약·판매·수출입·실적·리콜·인증
B=정책·무역·금융·외교·원자재·에너지·ESS·전력·UAM·항공·철도·조선·로봇
[스코어]
+3 주체가 A
+2 행위가 Act
+1 제목: 자동차 신호(자동차·차량·EV·차종·OEM·IVI·ADAS)
+1 차량용/자동차용/오토모티브/AEC-Q/ISO26262/리콜/NCAP
+1 A와 Act 동일 문장
+1 EV·HEV·PHEV·FCV/플랫폼(E-GMP·PPE·SSP·CMF)/규격(NACS·CCS)
-3 제목 B 중심(자동차 연결 없음)
-2 본문 B 중심(직접성 불명)
-2 배터리·반도체·소재·에너지: '차량용' 불명
-1 자동차 키워드 부차적
[판정 규칙]
total = 합계 게이트: total≥3 이면서 (① OEM/차종/차량용/규제·인증 신호 중 하나 명시 또는 ② A와 Act 동시문장) 일 때만 1, 그 외 0.""",

        "Lv2_균형_540자": """[역할] 뉴스클리핑 AI: 입력 기사 1건이 자동차와 직접 관련인지 분류.
[출력] "1" 또는 "0"만.
[집합]
A=완성차·OEM·전장·부품·타이어·충전·차량용EV배터리
Act=출시·양산·증설·생산·투자·수주·공급계약·판매·수출입·실적·리콜·인증
B=정책·무역·금융·원자재·에너지·ESS·전력·UAM·항공·철도·조선·로봇
[스코어]
+3 주체가 A
+2 행위가 Act
+1 제목: 자동차 신호(자동차·차량·EV·차종·OEM·IVI·ADAS)
+1 차량용/자동차용/오토모티브/AEC-Q/ISO26262/리콜/NCAP
+1 A와 Act 동일 문장
+1 EV·HEV·PHEV·FCV/플랫폼(E-GMP·PPE·SSP)/규격(NACS·CCS)
-3 제목 B 중심(자동차 연결 없음)
-2 본문 B 중심(직접성 불명)
-2 배터리·반도체·소재: '차량용' 불명
-1 자동차 키워드 부차적
[판정]
total≥3 이면서 (OEM/차종/차량용/규제·인증 중 하나 또는 A와Act 동시) 일 때만 1, 그 외 0""",

        "Lv3_적극_520자": """[역할] 뉴스클리핑 AI: 자동차 직접 관련 분류.
[출력] "1" 또는 "0"만.
[집합]
A=완성차·OEM·전장·부품·타이어·충전·차량용배터리
Act=출시·양산·증설·생산·투자·수주·공급계약·판매·수출입·실적·리콜·인증
B=정책·무역·금융·에너지·ESS·UAM·항공·철도·조선·로봇
[스코어]
+3 주체가 A
+2 행위가 Act
+1 제목: 차 신호(자동차·차량·EV·차종·OEM·IVI·ADAS)
+1 차량용/자동차용/오토모티브/AEC-Q/ISO26262/NCAP
+1 A와 Act 동일 문장
+1 EV·HEV·PHEV·FCV/플랫폼(E-GMP·PPE·SSP)/충전(NACS·CCS)
-3 제목 B 중심
-2 본문 B 중심
-2 배터리·반도체: 차량용 불명
-1 차 키워드 부차적
[판정]
total≥3 이면서 (OEM/차종/차량용/인증 중 하나 또는 A와Act 동시) 일 때만 1, 그 외 0"""
    }

    # 데이터 로드
    print("📂 데이터 로드 중...")
    df = pd.read_csv('data/samples.csv')
    print(f"✅ {len(df)}개 샘플 로드 완료")
    print(f"   - Label 1 (자동차): {sum(df['Label'] == 1)}개")
    print(f"   - Label 0 (비자동차): {sum(df['Label'] == 0)}개")

    # 전체 결과 저장
    all_results = {
        "evaluation_date": datetime.now().isoformat(),
        "evaluation_rules": EVALUATION_RULES,
        "prompt_results": {}
    }

    # 각 프롬프트 평가
    for prompt_name, prompt_text in PROMPTS.items():
        evaluator = PromptEvaluator(prompt_text, prompt_name)
        results = evaluator.run_evaluation(df)
        evaluator.print_summary()
        all_results["prompt_results"][prompt_name] = results

    # 최종 비교
    print(f"\n{'='*60}")
    print("📊 최종 비교")
    print(f"{'='*60}")

    best_prompt = None
    best_score = 0

    for name, results in all_results["prompt_results"].items():
        print(f"{name:20s} | 점수: {results['final_score']:.4f} | "
              f"정확도: {results['accuracy']:.4f} | 길이: {results['length']}자")

        if results['final_score'] > best_score:
            best_score = results['final_score']
            best_prompt = name

    print(f"\n🏆 최고 성능: {best_prompt} (점수: {best_score:.4f})")

    # 전체 결과 JSON 저장
    with open('results/evaluation_report.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print("\n📄 전체 평가 리포트 저장: results/evaluation_report.json")

    # 틀린 케이스 분석
    print(f"\n{'='*60}")
    print("🔍 공통 실패 패턴 분석")
    print(f"{'='*60}")

    common_failures = {}
    for name, results in all_results["prompt_results"].items():
        for case in results['detailed_analysis']['wrong_cases']:
            idx = case['index']
            if idx not in common_failures:
                common_failures[idx] = {
                    'title': case['title'],
                    'actual': case['actual'],
                    'failed_prompts': []
                }
            common_failures[idx]['failed_prompts'].append(name)

    # 모든 프롬프트가 틀린 케이스
    all_failed = [idx for idx, data in common_failures.items()
                  if len(data['failed_prompts']) == len(PROMPTS)]

    if all_failed:
        print(f"모든 프롬프트가 실패한 케이스 ({len(all_failed)}개):")
        for idx in all_failed[:3]:  # 처음 3개만
            print(f"  - Sample {idx}: {common_failures[idx]['title']}")
            print(f"    실제 라벨: {common_failures[idx]['actual']}")

if __name__ == "__main__":
    main()
