#!/usr/bin/env python3
"""
수동 테스트 - openai/gpt-oss-20b 모델 특성 반영
"""

import json
import csv
import requests
import time
from datetime import datetime

# API 설정
ENDPOINT = "http://203.234.62.45:1234/v1/chat/completions"
API_KEY = "lm-studio"
MODEL_NAME = "openai/gpt-oss-20b"

# v1.3 프롬프트
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

반드시 0또는1만 출력."""

def test_single(title, content=""):
    """단일 테스트 실행"""
    user_message = f"제목: {title}"
    if content:
        user_message += f"\n내용: {content}"
    
    try:
        response = requests.post(
            ENDPOINT,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            },
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 10,
                "temperature": 0
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content_response = result["choices"][0]["message"]["content"]
            reasoning_response = result["choices"][0]["message"].get("reasoning", "")
            
            # content나 reasoning에서 0 또는 1 찾기
            full_response = content_response + " " + reasoning_response
            
            if "1" in full_response and "0" not in full_response:
                classification = "1"
            elif "0" in full_response and "1" not in full_response:
                classification = "0"
            elif "1" in full_response:  # 둘 다 있으면 첫 번째로 나온 것
                classification = "1" if full_response.find("1") < full_response.find("0") else "0"
            else:
                classification = "0"  # 보수적 접근
                
            return classification, content_response, reasoning_response
        else:
            print(f"API 오류: {response.status_code}")
            return "0", "ERROR", "ERROR"
            
    except Exception as e:
        print(f"요청 실패: {str(e)}")
        return "0", "ERROR", "ERROR"

def main():
    print("🎯 openai/gpt-oss-20b 모델 테스트")
    print("=" * 50)
    
    # 테스트 케이스들
    test_cases = [
        {
            "title": "현대차, 1월 美판매 15% 늘어…역대 최대",
            "content": "현대자동차그룹이 올 1월 미국 시장에서 전년 동기 대비 15% 증가한 총 12만 5천여 대를 판매하며, 역대 1월 기준 월간 최다 판매 기록을 경신했다.",
            "expected": "1"
        },
        {
            "title": "네이버, AI 검색 서비스 업데이트",
            "content": "네이버가 인공지능 기반 검색 서비스를 대폭 개선했다고 발표했다.",
            "expected": "0"
        },
        {
            "title": "삼성SDI, 전기차 배터리 공장 건설",
            "content": "삼성SDI가 전기차용 배터리 생산 확대를 위해 새로운 공장 건설에 나선다.",
            "expected": "1"
        },
        {
            "title": "현대중공업, 선박 수주 증가",
            "content": "현대중공업이 올해 선박 수주량이 크게 늘었다고 발표했다.",
            "expected": "0"
        },
        {
            "title": "LG이노텍, 차량용 카메라 개발",
            "content": "LG이노텍이 자율주행차용 고성능 카메라 모듈을 개발했다.",
            "expected": "1"
        }
    ]
    
    correct = 0
    total = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n[테스트 {i}/{total}] {case['title'][:40]}...")
        print(f"예상 답: {case['expected']}")
        
        classification, content, reasoning = test_single(case['title'], case['content'])
        
        is_correct = classification == case['expected']
        if is_correct:
            correct += 1
        
        print(f"예측: {classification} {'✅' if is_correct else '❌'}")
        print(f"Content: '{content}'")
        print(f"Reasoning: '{reasoning}'")
        
        time.sleep(1)  # API 부하 방지
    
    print(f"\n" + "=" * 50)
    print(f"🎉 테스트 완료!")
    print(f"정확도: {correct}/{total} = {correct/total*100:.1f}%")
    
    if correct/total >= 0.8:
        print("✅ 기본 성능 확인! 전체 테스트 진행 가능")
    else:
        print("❌ 성능 부족. 프롬프트 조정 필요")

if __name__ == "__main__":
    main()