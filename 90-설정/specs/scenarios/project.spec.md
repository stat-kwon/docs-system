# 프로젝트 시나리오 Spec

## 트리거 키워드
- "프로젝트 시작", "실행 계획", "프로젝트 폴더"

## 워크플로우 요약
1. 사용자 확인: 폴더 생성과 다중 파일 생성을 진행해도 되는지 확인한다.
2. 템플릿 로드: `Filesystem:read_file("/90-설정/템플릿-Project.md")`.
3. 프론트매터 채우기: `status`, `priority`, `tags`, `projects`(자기 ID 포함), `moc_links`, `related_notes`를 작성한다 (`core/metadata.spec.md`).
4. 폴더/파일 생성: `/40-실행/{project_name}/` 폴더에 템플릿 기반 메인 파일을 생성하고, 계획/자료/작업 파일은 orchestrator의 `structure_files` 정보를 사용해 빈 템플릿을 작성한다.
5. 링크 구성: 메인 파일에 관련 Literature/Permanent/MOC 링크를 추가하고, 각 서브 파일에서도 프로젝트 메인 파일을 역링크한다.

## 메타데이터 집중 포인트
- `priority`: `low|medium|high|urgent` 중 하나 선택.
- `projects`: 배열 첫 번째 항목은 자기 `id`, 이후 관련 프로젝트 참조를 추가.
- `people`: 주요 참여자 이름 목록을 유지해 검색성을 높인다.
- `summary`: 프로젝트 목적을 한 줄로 요약.

## 콘텐츠 규칙
- `## ✅ 작업 목록` 섹션에 Tasks 형식(`- [ ]`)을 사용하고 due date/우선순위를 이모지로 표기한다.
- `/40-실행/{project_name}-작업.md` 파일에는 Dataview 쿼리나 진행 현황을 추가할 수 있도록 기본 구조를 제공한다.
- 프로젝트 종료 시 `status`를 `completed`, `updated` 날짜를 갱신하고 `summary`에 결과를 반영한다.

## 검증 체크리스트
- [ ] 폴더 구조(메인/계획/자료/작업)가 모두 생성되었다.
- [ ] 메타데이터 필수 필드(`status`, `priority`, `projects`)가 채워졌다.
- [ ] 관련 자료 링크 또는 TODO가 최소 2개 이상 있다.
- [ ] Tasks 섹션이 템플릿 구조를 유지한다.
- [ ] 프로젝트 메인 ↔ 서브 파일 간 역링크가 있다.

> Validator: `validators/priority.spec.md` + `core/metadata.spec.md`.
