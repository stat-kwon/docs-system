# 검색 시나리오 Spec

## 트리거 키워드
- "찾아줘", "보여줘", "검색"
- "관련 노트", "어디에 있어?"

## 검색 방법별 규칙

### 1. 태그 기반 검색
```dataview
TABLE file.name, file.tags
FROM #태그
SORT file.mtime DESC
```

### 2. 폴더 기반 검색
```bash
find 20-정리/핵심개념 -name "*.md" | head -10
```

### 3. 키워드 검색
```bash
grep -r "키워드" --include="*.md"
```

### 4. Dataview 쿼리 제공
```dataview
LIST
FROM "20-정리/핵심개념"
WHERE contains(tags, "ai")
LIMIT 10
```

## 검색 결과 표시

### 간단 표시
```markdown
## 검색 결과: "AI Agent"
- [[개념-20241024a-에이전트]]
- [[정리-20241023-AI시스템]]
- [[맵-AI시스템]]
```

### 상세 표시
```markdown
## 검색 결과: "AI Agent" (3건)

### 1. [[개념-20241024a-에이전트]]
- 타입: 핵심개념
- 태그: #ai/agent
- 수정일: 2024-10-24

### 2. [[정리-20241023-AI시스템]]
- 타입: 자료정리
- 출처: [[20241023-논문]]
- 수정일: 2024-10-23
```

## 검색 최적화 팁
- alias 활용으로 검색 확장
- 태그 계층구조 활용
- 명확한 파일명 사용

## 관련 노트 제안
```python
if 검색결과 < 3:
    suggest_similar_notes()
    suggest_related_tags()
```