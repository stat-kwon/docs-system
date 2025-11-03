# 메타데이터 Spec

## YAML Frontmatter 표준
```yaml
---
id: unique-identifier
title: "제목"
type: literature|permanent|moc|project|fleeting
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [hierarchical/tags]
status: pending|in-progress|completed
source: [[출처파일]]  # 자료정리/핵심개념 필수
aliases: [별칭1, 별칭2]
---
```

## 타입별 필수 필드

| 타입 | 필수 필드 |
|------|----------|
| fleeting | type, status, created |
| literature | type, source, created, tags |
| permanent | type, source, created, tags |
| moc | type, created, tags |
| project | type, status, created |

## 태그 규칙
- 소문자 사용: `#permanent`
- 단수형 사용: `#note` (O) / `#notes` (X)
- 계층 구조: `#tech/ai/llm`

## 템플릿 위치
- `/90-설정/템플릿-즉흥메모.md`
- `/90-설정/템플릿-Literature.md`
- `/90-설정/템플릿-Permanent.md`
- `/90-설정/템플릿-MOC.md`
- `/90-설정/템플릿-Project.md`