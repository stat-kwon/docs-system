# 메타데이터 Spec

## 공통 프론트매터 필드 (모든 노트)
| 필드 | 타입 | 설명 | 필수 | 템플릿 기본값 |
|------|------|------|------|----------------|
| `id` | string | 노트 고유 식별자 (타입 접두사 + 슬러그) | ✅ | 자동 플레이스홀더
| `title` | string | 화면에 노출되는 제목 | ✅ | 템플릿 변수 `{{title}}`
| `type` | enum | `literature`, `permanent`, `moc`, `project`, `fleeting` | ✅ | 시나리오별 고정값
| `created` | date | 최초 작성일 (`YYYY-MM-DD`) | ✅ | 오늘 날짜 플레이스홀더
| `updated` | date | 마지막 편집일 (`YYYY-MM-DD`) | ✅ | 오늘 날짜 플레이스홀더
| `status` | enum | 작업 상태 (`pending`, `in-progress`, `completed`, `archived`) | ✅ | 시나리오별 기본값
| `tags` | list | 계층형 태그 (`#domain/topic`) | ✅ | 빈 배열, 작성 시 채우기
| `aliases` | list | 대체 검색어 | 🔶 | 빈 배열
| `summary` | string | 한 줄 요약 (검색 스니펫) | 🔶 | 템플릿 주석으로 안내

## 검색 강화 필드 (공통 권장)
| 필드 | 설명 |
|------|------|
| `topics` | 주요 주제 키워드 배열 (예: `topics: ["ai", "context-engineering"]`)
| `people` | 관련 인물 (`people: ["Andy Matuschak"]`)
| `projects` | 연결된 프로젝트 ID 목록
| `moc_links` | 연결된 MOC 페이지 목록 (wikilink 문자열)
| `related_notes` | 연관된 노트 목록 (wikilink 문자열)
| `attachments_from_source` | 원문에서 가져온 첨부파일 이름 배열
| `source` | 원문 노트 wikilink 또는 URL (자료정리/핵심개념 필수)
| `url` | 외부 참고 링크 (literature/project 권장)
| `author` | 작성자/출처 인물명 (literature 필수)

## 타입별 요구사항
| 타입 | 필수 필드 | 권장 필드 |
|------|-----------|-----------|
| `fleeting` (즉흥메모) | `type`, `status`, `created`, `tags` | `summary`, `projects`
| `literature` | `type`, `source`, `created`, `tags`, `author`, `url`, `topics` | `moc_links`, `related_notes`, `attachments_from_source`
| `permanent` | `type`, `source`, `created`, `tags`, `moc_links` | `related_notes`, `topics`, `projects`
| `moc` | `type`, `created`, `tags`, `moc_links` (자기참조 허용) | `topics`, `projects`, `summary`
| `project` | `type`, `status`, `created`, `tags`, `priority`, `projects` (자기 ID 포함) | `people`, `moc_links`, `related_notes`

## 템플릿과의 연계
- 각 템플릿 프론트매터는 위 표의 필드를 모두 포함하고 있으며 기본값은 SSOT로 유지된다.
- 메타데이터를 변경하려면 **템플릿 파일을 수정**하고, 이 Spec의 표에 필드 설명을 동기화한다.
- 시나리오 Spec은 템플릿 경로와 필드 체크리스트만 안내하며, 구체 값/구조는 템플릿을 따른다.

## 작성 규칙
1. 날짜는 ISO `YYYY-MM-DD` 형식을 사용한다.
2. 태그는 모두 소문자, 단수형을 사용하고 `/`로 계층을 나타낸다 (`#ai/context`).
3. 리스트 필드는 `[]` 기본값을 유지하고, 값 추가 시 JSON 스타일로 입력한다 (`tags: ["ai/context"]`).
4. 새 필드 추가 시 Validator가 감지할 수 있도록 `/specs/validators`에 규칙을 추가한다.

## Dataview 최적화 팁
- `id`와 `type` 필드를 기준으로 뷰를 구성하면 템플릿 변경에도 쿼리가 안정적으로 유지된다.
- `summary` 필드가 존재하면 Dataview `TABLE summary` 구문으로 빠르게 프리뷰를 확인할 수 있다.
- `projects` 배열은 프로젝트 노트와 다른 노트를 양방향으로 연결하는 데 사용된다.

## 유지보수 체크리스트
- [ ] 새 템플릿 필드 추가 시 표 업데이트 완료
- [ ] Validator가 핵심 필드를 검사하는지 확인
- [ ] 시스템 프롬프트 요약이 템플릿 목록과 일치하는지 검토
