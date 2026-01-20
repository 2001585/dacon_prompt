"""
로컬 LLM을 사용한 프롬프트 평가
GPT-4o mini 대신 Ollama/LM Studio 등 로컬 모델 사용
"""

import pandas as pd
import json
import requests
import math
from typing import Dict, List
from datetime import datetime

# LM Studio 설정
USE_LM_STUDIO = True  # LM Studio 사용
LM_STUDIO_API_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "Llama-3.2-3B-Instruct-GGUF"

# Ollama 사용 시 (백업)
OLLAMA_API_URL = "http://localhost:11434/api/generate"

def call_ollama(prompt: str, user_input: str) -> str:
    """Ollama API 호출"""
    payload = {
        "model": MODEL_NAME,
        "prompt": f"{prompt}\n\n[기사]\n{user_input}",
        "stream": False,
        "options": {
            "temperature": 0.1,  # 일관성을 위해 낮게 설정
            "top_p": 0.1
        }
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        result = response.json()
        return result['response'].strip()
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return "0"

def call_lm_studio(prompt: str, user_input: str) -> str:
    """LM Studio API 호출 (OpenAI 호환)"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"[기사]\n{user_input}"}
        ],
        "temperature": 0.1,
        "max_tokens": 10
    }

    try:
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            headers=headers,
            json=payload
        )
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error calling LM Studio: {e}")
        return "0"

def calculate_dacon_score(accuracy: float, prompt_length: int) -> float:
    """데이콘 공식 점수 계산"""
    if prompt_length <= 300:
        length_score = 1.0
    else:
        length_score = math.sqrt(1 - ((prompt_length - 300) / 2700) ** 2)

    return 0.9 * accuracy + 0.1 * length_score

def evaluate_prompt(prompt_name: str, prompt_text: str, df: pd.DataFrame) -> Dict:
    """프롬프트 평가"""
    correct = 0
    predictions = []
    errors = []
    detailed_results = []  # 각 샘플별 상세 결과

    print(f"\n평가 중: {prompt_name} ({len(prompt_text)}자)")
    print("-" * 50)

    for idx, row in df.iterrows():
        title = row['title']
        content = row['content']
        actual = row['label']

        user_input = f"제목: {title}\n본문: {content}"

        # LLM 호출
        if USE_LM_STUDIO:
            response = call_lm_studio(prompt_text, user_input)
        else:
            response = call_ollama(prompt_text, user_input)

        # 응답에서 0 또는 1 추출
        if "1" in response[:10]:  # 처음 10자 내에서 찾기
            predicted = 1
        elif "0" in response[:10]:
            predicted = 0
        else:
            predicted = 0  # 기본값

        predictions.append(predicted)

        # 각 샘플별 상세 결과 저장
        is_correct = (predicted == actual)
        sample_id = row.get('ID', row.get('id', idx))  # ID 또는 id 또는 인덱스
        detailed_results.append({
            'id': sample_id,
            'title': title[:80],
            'actual': actual,
            'predicted': predicted,
            'correct': is_correct,
            'response': response[:100]  # LLM 원본 응답 일부
        })

        if is_correct:
            correct += 1
        else:
            errors.append({
                'id': sample_id,
                'title': title[:50],
                'actual': actual,
                'predicted': predicted
            })

        # 진행상황 표시 - 각 샘플마다 결과 출력
        status_symbol = "O" if is_correct else "X"
        print(f"  [{status_symbol}] Sample {sample_id:2}: 실제={actual}, 예측={predicted} - {title[:40]}...")

        # 10개마다 요약
        if (idx + 1) % 10 == 0:
            print(f"  >>> 진행: {idx + 1}/{len(df)} - 현재 정확도: {correct/(idx+1):.2%}")

    accuracy = correct / len(df)
    prompt_length = len(prompt_text)
    dacon_score = calculate_dacon_score(accuracy, prompt_length)

    return {
        'name': prompt_name,
        'length': prompt_length,
        'accuracy': accuracy,
        'correct': correct,
        'total': len(df),
        'dacon_score': dacon_score,
        'errors': errors[:5],  # 상위 5개 오류만
        'detailed_results': detailed_results  # 전체 상세 결과
    }

# 테스트할 프롬프트들
PROMPTS_TO_TEST = {
    "김경태_원본": """[역할] 뉴스클리핑 AI: 입력 기사 1건이 자동차와 직접 관련인지 분류.
[출력] "1" 또는 "0"만.
[집합]
A=완성차·OEM·전장·부품·타이어·충전·차량용EV배터리
Act=출시·양산·증설·생산·투자·수주·공급계약·판매·수출입·실적·리콜·인증
B=정책·무역·금융·외교·원자재·에너지·ESS·전력·UAM·항공·철도·조선·로봇
[스코어] (중복 가산 금지)
+3 주체가 A에 속함
+2 행위가 Act에 속함
+1 제목: 자동차 신호(자동차·차량·EV·차종·OEM·IVI·ADAS)
+1 차량용/자동차용/오토모티브/AEC-Q/ISO26262/리콜/NCAP·KNCAP·NHTSA
+1 A와 Act 동일 문장(근접)
+1 EV·HEV·PHEV·FCV/플랫폼(E-GMP·PPE·SSP·CMF)/규격(NACS·CCS)
-3 제목 B 중심(자동차 연결 없음)
-2 본문 B 중심(직접성 불명)
-2 배터리·반도체·소재·에너지: '차량용' 불명
-1 자동차 키워드 부차적
[판정 규칙]
total = 합계 게이트: total≥3 이면서 (① OEM/차종/차량용/규제·인증 신호 중 하나 명시 또는 ② A와 Act 동시문장) 일 때만 1, 그 외 0. (모호하면 0)""",

    "M12_축약스코어링": """[車분류]"1"또는"0"만
[집합]
A=완성차·OEM·전장·부품·타이어·충전·車배터리
Act=출시·양산·생산·투자·수주·공급계약·판매
B=정책·무역·ESS·UAM·항공·철도·조선
[점수]
+3 주체∈A
+2 행위∈Act
+1 차량용명시
+1 A∧Act동시
-3 B중심
-2 차량용불명
[판정]
합≥3∧(차량용||A∧Act)→1
else→0""",

    "V2_Gamma_영어": """Auto industry primary=1, Other=0

TEST: Auto engineers target audience?
YES=1, NO=0

AUTO(1):
-Vehicle mfg/sales/tech
-Auto parts for vehicles
-Vehicle services

OTHER(0):
-Energy biz(ESS/home)
-Policy/trade
-Industrial apps

KEY:
"Tesla vs energy co"=Energy=0
"Tesla new car"=Auto=1
"EV battery mfg"=Auto=1
"Home battery"=Energy=0

Output: "1" or "0" only"""
}

def main():
    """메인 실행"""
    # 샘플 데이터 로드
    df = pd.read_csv('data/samples.csv')
    print(f"샘플 데이터 로드: {len(df)}개")
    print(f"레이블 분포: 1={sum(df['label']==1)}개, 0={sum(df['label']==0)}개")

    # 모델 연결 테스트
    print(f"\n모델 연결 테스트 (Model: {MODEL_NAME})...")
    if USE_LM_STUDIO:
        test_response = call_lm_studio("답변: 1", "테스트")
        print(f"LM Studio 연결 성공! 테스트 응답: {test_response}")
    else:
        test_response = call_ollama("답변: 1", "테스트")
        print(f"Ollama 연결 성공! 테스트 응답: {test_response}")

    # 자동 실행 모드
    print("\n평가를 시작합니다...")
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--no-auto':
        if input("계속하시겠습니까? (y/n): ").lower() != 'y':
            return

    # 각 프롬프트 평가
    results = []
    for prompt_name, prompt_text in PROMPTS_TO_TEST.items():
        result = evaluate_prompt(prompt_name, prompt_text, df)
        results.append(result)

        print(f"\n결과: {prompt_name}")
        print(f"  정확도: {result['accuracy']:.2%} ({result['correct']}/{result['total']})")
        print(f"  예상 점수: {result['dacon_score']:.4f}")

        if result['errors']:
            print("  주요 오류:")
            for err in result['errors'][:3]:
                print(f"    - ID{err['id']}: {err['title']} (실제:{err['actual']}, 예측:{err['predicted']})")

    # 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results/local_llm_results_{MODEL_NAME.replace(':', '_')}_{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {filename}")

    # 최종 순위
    print("\n" + "=" * 60)
    print("최종 순위")
    print("=" * 60)
    results.sort(key=lambda x: x['dacon_score'], reverse=True)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']}: {result['dacon_score']:.4f} (정확도: {result['accuracy']:.2%}, 길이: {result['length']}자)")

if __name__ == "__main__":
    main()
