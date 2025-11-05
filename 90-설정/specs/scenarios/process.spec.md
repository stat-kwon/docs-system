# 프로세스 시나리오 Spec (자료정리)

## 트리거 키워드
- "정리해줘", "요약해줘", "분석해줘"
- "자료정리 만들어줘", "이해하고 정리"

## 워크플로우 요약
1. 원문 확인: `/10-수집/원문/`에서 대응하는 원문 노트를 찾는다.
2. 템플릿 로드: `Filesystem:read_file("/90-설정/템플릿-Literature.md")` (SSOT).
3. 프론트매터 채우기: 템플릿에 있는 모든 필드 유지, `source`, `author`, `url`, `topics`, `attachments_from_source`를 반드시 채운다. 세부 설명은 `core/metadata.spec.md` 참조.
4. 본문 작성: 템플릿 섹션(메타정보/핵심 요약/주요 개념/인사이트/다음 단계)을 그대로 사용하고 주석을 따라 채운다.
5. 저장: `/20-정리/자료정리/정리-YYYYMMDD-주제.md` 경로에 저장한다.

## 메타데이터 집중 포인트
- `source`: 원문 노트 wikilink (예: `[[20241024-claude]]`).
- `author`, `url`: 검색 및 필터링을 위한 필수 필드.
- `topics`: 최대 3개의 주제 키워드를 추가하여 Dataview 검색 품질을 높인다.
- `moc_links`: 관련 MOC가 있다면 wikilink 배열로 추가한다.
- `attachments_from_source`: 원문 YAML에 `attachments`가 있으면 동일 목록을 복사한다.

## 링크 & 첨부 규칙
- 본문 `## 메타정보` 섹션에 `**출처**: [[원문]]`을 명시한다.
- 첨부파일은 `/80-보관/첨부파일/YYYYMMDD/` 아래 상대경로 `![]()`로 참조한다.
- 핵심 개념을 발견하면 `## 다음 단계` 체크리스트에 후보 개념을 기록한다.

## 검증 체크리스트 (validator 연계)
- [ ] `source` 필드가 존재하고 실제 원문 파일이 있다.
- [ ] 저장 폴더/파일명이 규칙을 따른다.
- [ ] `topics` 배열이 비어있지 않다.
- [ ] `attachments_from_source`가 원문과 동기화되어 있다.
- [ ] 본문 섹션이 템플릿 순서를 유지한다.

> 검증은 `validators/link-validator.spec.md`와 `core/metadata.spec.md`의 규칙을 따른다. 오류가 발생하면 템플릿을 우선 업데이트하고 재생성한다.
