# SynthPanel — LLM 페르소나 기반 병렬 사용성 테스트 도구

바이브 코딩된 웹앱 URL을 주면, **N개의 가상 사용자 페르소나**가 각자의 목표·성향·기술수준을
가지고 실제 브라우저(Playwright)를 **병렬로** 조작하며 앱을 사용한다. 마치 클로즈드 베타처럼
돌려서 **버그·UX 마찰·정성 피드백**을 자동 수집한다.

---

## 1. 목표

- 사람 모집 없이, 다양한 사용자 페르소나로 **사용성 테스트를 자동화**한다.
- 결과로 **버그 리포트**, **UX 피드백**, **세션 트레이스**, **집계 대시보드**를 만든다.
- 바이브 코딩으로 빠르게 만든 앱의 사각지대(엣지케이스 사용자, 저숙련, 접근성 등)를 드러낸다.

## 2. 핵심 루프 (한 페르소나의 1 스텝)

```
관찰(Observe) → 추론(Think) → 행동(Act) → 검증(Verify)
```

1. **Observe**: 현재 페이지의 접근성 트리(snapshot) + URL/title + 콘솔/네트워크/JS 에러를 수집.
   멀티모달 모델 + `--vision` 지정 시 스크린샷도 첨부.
2. **Think**: LLM이 페르소나 프롬프트 + 현재 목표 + 관찰 결과를 받아 다음 행동을
   **구조화 JSON**으로 결정 (`click`, `type`, `navigate`, `scroll`, `wait`, `assert`,
   `note`, `report_bug`, `done`, `give_up`).
3. **Act**: 결정된 액션을 Playwright로 실행. 요소 지정은 접근성 트리의 안정적 ref(역할+이름) 기반.
4. **Verify**: 액션 후 변화 감지. 에러/예외/무반응이면 LLM이 버그 후보로 판단하고 트레이스에 기록.

종료 조건: 목표 달성(`done`), 포기(`give_up`), max-steps 초과, 치명적 에러.

## 3. 아키텍처 (Python + asyncio)

```
synthpanel/
├─ cli.py                # 진입점: synthpanel run/init
├─ config.py             # 설정/모델/env 로딩 (pydantic-settings)
├─ orchestrator.py       # N개 세션 asyncio.gather + Semaphore 동시성 제어
├─ web/                  # 로컬 웹 앱 (FastAPI + HTMX/Jinja)
│   ├─ app.py            # FastAPI 라우트 (온보딩 a~f 플로우)
│   ├─ store.py          # SQLite: settings / projects / runs (~/.synthpanel)
│   ├─ templates/        # Jinja 템플릿 (welcome, provider, project, run)
│   └─ static/           # CSS 등
├─ persona/
│   ├─ models.py         # Persona 스키마 (5차원 팩터)
│   ├─ factors.py        # 5차원 팩터 정의·검증·기본값
│   ├─ recommender.py    # 도메인 분석 → 패널 자동 추천 (엣지케이스 포함)
│   ├─ generator.py      # LLM으로 페르소나 N개 생성 / YAML 로드
│   └─ library/          # 사전 정의 archetype YAML
├─ agent/
│   ├─ loop.py           # Observe-Think-Act-Verify 루프
│   ├─ llm.py            # LLM provider 추상화 (Anthropic / Fake)
│   ├─ actions.py        # 액션 스키마 + Playwright 실행 매핑
│   └─ prompts.py        # 시스템/스텝 프롬프트 템플릿
├─ browser/
│   ├─ session.py        # BrowserContext 1개 = 페르소나 1명 (격리)
│   ├─ observer.py       # 접근성 트리 직렬화, 콘솔/네트워크/JS에러 후킹
│   └─ vision.py         # 스크린샷 캡처 (옵션)
├─ report/
│   ├─ trace.py          # 스텝별 trace(JSONL) + Playwright trace.zip + 비디오
│   ├─ bug.py            # 버그 스키마(재현단계/심각도/스크린샷)
│   ├─ aggregate.py      # 다수 세션 → 공통 이슈 클러스터링/우선순위
│   └─ render.py         # Markdown + 자체 HTML 대시보드 생성
└─ tests/
```

**격리**: 한 단일 `Browser`에서 페르소나마다 별도 `BrowserContext`(쿠키/스토리지 격리) 생성
→ 가볍고 진짜 동시 사용자처럼 동작. 동시성은 `asyncio.Semaphore`로 상한 제어
(LLM rate limit·CPU 보호).

## 4. 페르소나 팩터 모델 (5차원)

각 팩터는 LLM 자동 생성·수동 선택 모두 가능. 팩터별 `weight`로 행동 영향도를 조절한다.

**① 인구통계 (Demographics)**
- 나이대 · 성별 · 거주 지역/국가 · 도시규모(대도시/소도시/농촌)
- 모국어/사용언어 · 학력 · 직업/업종 · 소득구간 · 가구형태

**② 디지털 리터러시 (Tech profile)**
- 기술 숙련도(1–5) · 주 사용 기기(모바일/데스크톱/태블릿) · OS/브라우저
- 네트워크 환경(고속/3G 스로틀) · 접근성 요구(스크린리더·저시력·색각·운동성)
- 유사 앱 경험 · 입력 선호(키보드/마우스/터치)

**③ 행동·심리 (Psychographics)**
- 인내심/좌절 내성 · 탐색 스타일(훑기형/꼼꼼형/목표지향형)
- 디테일 주의도 · 의사결정 속도(충동/신중) · 설명문 읽는 정도
- 신뢰/의심 성향 · 기본 감정상태

**④ 가치관·태도 (Attitudes)** — 민감 팩터, 항상 선택 가능
- 정치 관여/성향 · 프라이버시 민감도 · 가격 민감도 · 신기술 수용도
- 브랜드 충성도 · 사회/환경 가치

**⑤ 맥락·목표 (Intent / scenario)**
- 달성하려는 목표(job-to-be-done) · 방문 맥락(첫방문/재방문/광고유입)
- 시간 여유(급함/여유) · 동기 수준 · 성공 기준

> **편향·윤리 가드레일**: 정치·소득·종교 같은 민감 팩터는 항상 켜고 끌 수 있지만,
> 캐리커처/고정관념화하지 않도록 프롬프트에서 "현실적 사용 행동에만 영향"을 강제한다.

### 데이터 모델 (요지)

- **Persona**: `name, archetype, demographics, tech, psych, attitudes, intent, factor_weights`
- **Action**: `type, target_ref?, value?, rationale` (LLM 출력, tool-use로 검증)
- **StepTrace**: `step_idx, observation_digest, action, result, screenshot?, ts`
- **BugReport**: `title, severity(critical/major/minor), repro_steps[], expected, actual, persona, screenshot, console_errors[]`
- **SessionResult**: `persona, status(success/failed/gaveup), steps[], bugs[], ux_feedback`

```yaml
# personas.yaml (예시 1명)
- name: "김순자"
  archetype: "디지털 입문 고령 사용자"
  demographics: { age_band: "65-74", gender: F, region: "대구", city_tier: metro, education: highschool }
  tech: { savviness: 2, device: mobile, os: android, network: "3g_throttled", a11y: ["large_text"] }
  psych: { patience: low, exploration: methodical, reads_instructions: high }
  attitudes: { privacy_sensitivity: high }
  intent: { goal: "손주에게 송금하기", context: first_visit, time_pressure: relaxed }
  factor_weights: { "tech.savviness": 0.9, "psych.patience": 0.8 }
```

## 5. 프로젝트 시작 플로우 (`synthpanel init`)

기본은 **자동 추천 전체**: URL/앱 설명을 LLM이 분석 → 타깃 오디언스 추론 →
**균형 잡힌 패널 N명**을 제안(엣지케이스 포함). 사용자는 카드로 검토/수정/교체/잠금.
결과는 `personas.yaml`로 저장(버전관리·재사용·공유).

옵션 모드:
- **Build**: 팩터별 값/슬라이더로 한 명씩 구성하거나 라이브러리에서 선택.
- **하이브리드**: archetype 몇 개만 고르면 나머지 팩터는 LLM이 채움.

## 6. 리포트 (4종 전부)

1. **버그/이슈 목록** — 심각도·재현단계·스크린샷 포함 (JSON + Markdown)
2. **UX 피드백** — 페르소나별 주관적 사용성 코멘트, 혼란 지점, 감정 반응
3. **세션 기록/트레이스** — 행동 JSONL + Playwright trace.zip + 비디오(옵션)
4. **집계 대시보드** — 여러 세션 결과를 임베딩/LLM으로 클러스터링해 공통 문제·우선순위를 보여주는 정적 HTML

## 7. LLM 계층

- 기본 모델: `claude-opus-4-8`(추론·버그판단), 경량 스텝엔 `claude-haiku-4-5` 옵션.
- **tool-use 기반 structured output**으로 액션 강제 → 파싱 실패 최소화.
- 비전: `--vision` + 멀티모달 모델 지정 시 스크린샷 첨부. 미지정 시 DOM/접근성 트리만.
- `ANTHROPIC_API_KEY`는 env 주입. LLM 클라이언트는 인터페이스로 추상화하고
  **Fake provider**로 API 없이 로컬 테스트 가능.

## 8. CLI 사용 예

```bash
# 패널 구성
synthpanel init --url https://my-vibe-app.dev --personas 8 --out personas.yaml

# 테스트 실행
synthpanel run \
  --url https://my-vibe-app.dev \
  --personas personas.yaml \
  --max-steps 25 \
  --concurrency 4 \
  --model claude-opus-4-8 \
  --vision \
  --out ./reports/run-2026-06-16
```

## 9. 로컬 웹 앱 & 온보딩 플로우

`synthpanel serve`로 로컬 웹 서버를 띄우고 브라우저로 접속한다. 스택은
**FastAPI + HTMX/Jinja**(별도 JS 빌드 없음), 로컬 상태는 **SQLite (`~/.synthpanel/synthpanel.db`)**.

```
[serve] → 브라우저 접속
  (a) Welcome → "Get Started"
  (b) LLM Provider 선택: Claude(Anthropic) / OpenAI(Codex) / 로컬(Ollama)   ※ Claude 먼저
  (c) 설정값 입력(API key·base URL·모델) → "연결 테스트" → 성공 시 로컬 저장
       └ 다음 세션부터 마지막 설정을 기본값으로 자동 적용하고 (b)(c) 스킵
  (d) 프로젝트 유무 분기
       ├ 없음 → 바로 프로젝트 생성
       └ 있음 → 프로젝트 목록(선택해 다른 설정으로 재실행 / 재실행)
  (e) 프로젝트 생성: URL + 테스트 방식/중점(focus) + 대상 페르소나 결정
  (f) 프로젝트 상세 → 여기서 Test 실행, 실행 이력·리포트 확인
```

- **Provider 추상화**: 각 provider는 `(label, 설정 필드, 기본 모델, test_connection)`을 노출.
  `LLMProvider` 프로토콜 덕에 엔진은 provider 종류와 무관하게 동작.
- **연결 테스트**: 저장 전 최소 호출로 키/모델 유효성 확인. 실패 시 저장 안 함.
- **저장 모델(SQLite)**: `settings`(마지막 provider 설정), `projects`(url/focus/personas),
  `runs`(실행 이력 + 결과 JSON).

## 10. 구현 단계 (점진적, 각 단계 동작 가능)

1. **스캐폴딩**: 프로젝트 구조, `pyproject.toml`, README, PLAN.md.
2. **브라우저 코어**: 단일 페르소나로 URL 열고 접근성 트리 직렬화 + 콘솔/네트워크 에러 후킹.
3. **에이전트 루프(Fake LLM)**: 결정론적 fake provider로 Observe-Think-Act 루프 + 액션 실행 검증.
4. **실제 LLM 연동**: Anthropic tool-use 액션, 프롬프트 템플릿, 버그/완료 판단.
5. **페르소나 생성/로딩**: 5차원 팩터, YAML 라이브러리 + LLM 추천기 + `init` 플로우.
6. **병렬 오케스트레이터**: N 세션 동시 실행, 동시성/타임아웃/재시도.
7. **로컬 웹 앱**: FastAPI + HTMX/Jinja 온보딩 플로우(a~f), SQLite 저장, provider
   연결 테스트, 프로젝트 생성/상세/실행.
8. **리포팅**: trace/bug/ux 수집 → Markdown + HTML 대시보드 + 집계 클러스터링.
9. **비전 모드 + 다듬기**: 스크린샷 첨부 경로, 비용/토큰 로깅, 데모용 샘플 앱.

## 11. PR 진행

- PR1 (완료): 단계 1~3 — 스캐폴딩 + 브라우저 코어 + Fake LLM 루프.
- PR2 (현재): 단계 7 — 로컬 웹 앱 온보딩 플로우 + SQLite + provider 설정/연결 테스트 +
  프로젝트 CRUD + 실행. API 키 없이도 Fake provider로 전체 플로우가 도는 상태로 유지.
