@echo off
set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%\..\.."

echo =================================================
echo 로컬 LLM 평가 시작
echo =================================================
echo.
echo LM Studio가 실행 중이어야 합니다 (포트: 1234)
echo Llama-3.2-3B-Instruct 모델이 로드되어 있어야 합니다
echo.
pause

python scripts\evaluation\local_llm_evaluation.py

echo.
echo =================================================
echo 평가 완료! 결과 분석 시작
echo =================================================
echo.

python scripts\analysis\analyze_results.py

echo.
echo 모든 작업 완료!
pause

popd
