# SynthPanel

LLM 페르소나 기반 **병렬 사용성 테스트** 도구. 바이브 코딩된 웹앱 URL을 주면,
N개의 가상 사용자 페르소나가 각자의 목표·성향·기술수준을 가지고 실제 브라우저(Playwright)를
병렬로 조작하며 앱을 사용한다. 마치 클로즈드 베타처럼 돌려서 **버그·UX 마찰·정성 피드백**을
자동 수집한다.

전체 설계는 [PLAN.md](./PLAN.md) 참고.

## 상태

초기 스캐폴딩 (단계 1~3). API 키 없이도 Fake LLM provider로 전체 에이전트 루프가 돈다.

- ✅ 페르소나 5차원 팩터 모델
- ✅ 액션 스키마 + Playwright 매핑
- ✅ 브라우저 observer (접근성 트리 + 콘솔/네트워크/JS 에러)
- ✅ Observe-Think-Act-Verify 에이전트 루프
- ✅ Fake / Anthropic LLM provider 추상화
- ⏳ 실제 LLM tool-use, 병렬 오케스트레이터, 리포트 대시보드 (다음 PR)

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
