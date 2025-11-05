# 📚 docs-system 운영 가이드 (Claude Desktop)

## 1. 필수 명령 흐름
1. **시나리오 결정** 후 즉시 한 번만 호출:  
   `python3 orchestrator.py workflow <scenario> '<title>'`
2. 응답에는 다음이 포함된다.
   - `specs`: 시나리오별 Spec 번들과 총 라인 수
   - `template`: 템플릿 절대 경로와 라인 수 (SSOT)
   - `validation_rules` + `validator_specs`
   - `context_lines`: 현재 로드 라인 수와 목표(`270`)
3. 필요한 경우 `workflow["template"]["path"]`를 `Filesystem:read_file`로 불러와 문서를 작성한다.
4. 파일을 생성/수정한 후 `python3 orchestrator.py validate <path>`로 검증한다 (`--quick` 옵션은 Validator 생략).

> 추가 호출이 필요하면 같은 `workflow` 응답을 재사용한다. `get_scenario_info`/`get_filename`을 개별 호출하지 않는다.

## 2. 시나리오 요약 (SSOT ↔ 템플릿 매핑)
| 시나리오 | 주요 목적 | 저장 경로 | 템플릿 | Validator |
|----------|-----------|-----------|---------|-----------|
| `capture` | 즉흥 아이디어/할일 기록 | `/10-수집/즉흥메모/` | `템플릿-즉흥메모.md` | `validators/priority.spec.md` |
| `process` | 원문 분석 자료정리 | `/20-정리/자료정리/` | `템플릿-Literature.md` | `validators/link-validator.spec.md` |
| `create` | 핵심개념 (100줄 이하) | `/20-정리/핵심개념/` | `템플릿-Permanent.md` | `validators/link-validator.spec.md` |
| `connect` | 주제별 MOC 허브 | `/30-연결/` | `템플릿-MOC.md` | `validators/link-validator.spec.md` |
| `project` | 실행 계획 및 추적 | `/40-실행/{project}` | `템플릿-Project.md` | `validators/priority.spec.md` |
| `review` | 주기적 회고 (읽기 전용) | `/50-회고/` 등 | Spec만 참고 | - |
| `search` | 탐색/정보 조회 | - | - | - |

세부 단계는 각 시나리오 Spec(`specs/scenarios/*.spec.md`)에서 확인한다. 문서 구조/메타데이터 변경은 **반드시 템플릿 파일**을 수정하여 반영한다.

## 3. 메타데이터 원칙
- 프론트매터 필드는 `specs/core/metadata.spec.md`의 표를 따른다.
- 템플릿에는 `summary`, `topics`, `people`, `projects`, `moc_links`, `related_notes` 등 검색 친화 필드가 기본 포함되어 있다. 값을 빈 배열로 남기지 말고 가능한 만큼 채운다.
- `id`는 타입 접두사를 포함하도록 템플릿에서 자동 생성된다. 필요 시 사람이 읽기 쉬운 슬러그로 수정한다.
- 태그는 소문자/단수형/계층 구조(`tags: ["ai/context"]`).
- 원문 첨부 파일 사용 시 `/80-보관/첨부파일/YYYYMMDD/` 위치를 참조하고 `attachments_from_source` 배열을 업데이트한다.

## 4. 파일/링크 규칙 요약
- 모든 문서는 `.md`. Obsidian wikilink(`[[...]]`) 사용.
- 핵심개념은 최소 1개의 MOC, 자료정리는 원문을 `source`와 본문에 모두 링크한다.
- 프로젝트 하위 파일(계획/자료/작업)은 메인 노트와 양방향 링크를 유지한다.
- Validator 경고가 나오면 해당 Spec/템플릿을 참고하여 수정한다.

## 5. 컨텍스트 관리
- `workflow` 응답의 `context_lines.total`이 `context.target_total_lines`(270)을 초과하면 세부 Spec/Validator를 재검토하거나 `--quick` 검증을 사용한다.
- 새로운 필드나 섹션을 도입할 때는 라인 수 영향과 중복 여부를 확인하고, 가능하면 템플릿/코어 Spec을 수정하여 재사용한다.

## 6. 안전 장치
- `/10-수집/원문/` 내 원문 파일은 읽기 전용.
- 파일 삭제/병합/대규모 이동은 사람에게 확인 후 진행.
- 자동화로 데이터 손실 가능성이 있으면 반드시 사용자에게 질문한다.
