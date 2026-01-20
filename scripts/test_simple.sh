#!/bin/bash

# v1.3 시스템 프롬프트
SYSTEM_PROMPT='뉴스 자동차 관련 분류 전문가. 출력: 관련(1), 무관(0)만.

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

반드시 0또는1만 출력.'

echo "🔍 v1.3 프롬프트 테스트"
echo "=========================="

# 테스트 케이스 1: 현대차 (확실한 1)
echo -e "\n[테스트 1] 현대차 뉴스"
USER_MSG1='제목: 현대차, 1월 美판매 15% 늘어…역대 최대
내용: 현대자동차그룹이 올 1월 미국 시장에서 전년 동기 대비 15% 증가한 총 12만 5천여 대를 판매하며, 역대 1월 기준 월간 최다 판매 기록을 경신했다.'

RESULT1=$(curl -s -X POST http://203.234.62.45:1234/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer lm-studio" \
-d '{
"model":"openai/gpt-oss-20b",
"messages":[
{"role":"system","content":"'"$SYSTEM_PROMPT"'"},
{"role":"user","content":"'"$USER_MSG1"'"}
],
"max_tokens":3,
"temperature":0
}' | jq -r '.choices[0].message.content')

echo "응답: '$RESULT1'"

# 테스트 케이스 2: 네이버 (확실한 0)  
echo -e "\n[테스트 2] 네이버 뉴스"
USER_MSG2='제목: 네이버, AI 검색 서비스 업데이트
내용: 네이버가 인공지능 기반 검색 서비스를 대폭 개선했다고 발표했다.'

RESULT2=$(curl -s -X POST http://203.234.62.45:1234/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer lm-studio" \
-d '{
"model":"openai/gpt-oss-20b",
"messages":[
{"role":"system","content":"'"$SYSTEM_PROMPT"'"},
{"role":"user","content":"'"$USER_MSG2"'"}
],
"max_tokens":3,
"temperature":0
}' | jq -r '.choices[0].message.content')

echo "응답: '$RESULT2'"

# 테스트 케이스 3: 삼성SDI 배터리 (경계케이스)
echo -e "\n[테스트 3] 삼성SDI 배터리 뉴스"
USER_MSG3='제목: 삼성SDI, 전기차 배터리 공장 건설
내용: 삼성SDI가 전기차용 배터리 생산 확대를 위해 새로운 공장 건설에 나선다.'

RESULT3=$(curl -s -X POST http://203.234.62.45:1234/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer lm-studio" \
-d '{
"model":"openai/gpt-oss-20b",
"messages":[
{"role":"system","content":"'"$SYSTEM_PROMPT"'"},
{"role":"user","content":"'"$USER_MSG3"'"}
],
"max_tokens":3,
"temperature":0
}' | jq -r '.choices[0].message.content')

echo "응답: '$RESULT3'"

echo -e "\n=========================="
echo "테스트 완료!"