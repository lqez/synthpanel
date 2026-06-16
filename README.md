# SynthPanel

LLM 페르소나 기반 **병렬 사용성 테스트** 도구. 바이브 코딩된 웹앱 URL을 주면,
N개의 가상 사용자 페르소나가 각자의 목표·성향·기술수준을 가지고 실제 브라우저(Playwright)를
병렬로 조작하며 앱을 사용한다. 마치 클로즈드 베타처럼 돌려서 **버그·UX 마찰·정성 피드백**을
자동 수집한다.

전체 설계는 [PLAN.md](./PLAN.md) 참고.

## 상태

엔진 + 로컬 웹 앱 온보딩 플로우. API 키 없이도 Fake provider로 전체 플로우가 돈다.

- ✅ 페르소나 5차원 팩터 모델
- ✅ 액션 스키마 + Playwright 매핑
- ✅ 브라우저 observer (접근성 트리 + 콘솔/네트워크/JS 에러)
- ✅ Observe-Think-Act-Verify 에이전트 루프
- ✅ LLM provider 추상화 + 실제 Anthropic tool-use provider
- ✅ 로컬 웹 앱 (FastAPI + HTMX/Jinja): Welcome → Provider 설정/연결테스트 →
  프로젝트 생성/상세 → 테스트 실행 → 결과
- ✅ SQLite 로컬 저장 (`~/.synthpanel/synthpanel.db`): 설정/프로젝트/실행이력
- ✅ 페르소나 자동 추천기 (엣지케이스 포함, 프로젝트 생성에 통합)
- ✅ 병렬 오케스트레이터 (Semaphore + asyncio.gather)
- ✅ 리포트: 버그 집계 클러스터링 + Markdown/HTML 대시보드
- ✅ 실시간 진행: 백그라운드 실행 + SSE 스트리밍

## 웹 앱 실행

```bash
synthpanel serve            # http://127.0.0.1:8000
playwright install chromium # 실제 테스트 실행 시 (Fake provider는 불필요)
```

플로우: Welcome → "Get Started" → LLM provider 선택·설정·연결 테스트(성공 시 로컬 저장,
다음부터 자동 적용) → 프로젝트 생성(URL·focus·페르소나) → 프로젝트 상세에서 테스트 실행.

## 설치

```bash
pip install -e ".[dev]"
playwright install chromium   # 브라우저 코어 사용 시
```

## 개발

```bash
pytest                # Fake provider 기반 단위 테스트 (브라우저/네트워크 불필요)
```

## CLI (초기)

```bash
synthpanel version
synthpanel run --url https://example.com --persona-name "김순자" --max-steps 10 --provider fake
```

> 실제 LLM 연동·병렬 실행·리포트 생성은 후속 단계에서 추가됩니다.
