# 연결 시나리오 Spec (MOC)

## 트리거 키워드
- "MOC 만들어줘", "맵 생성"
- "주제 연결", "개념 구조화"

## MOC 생성 규칙

### 1. 템플릿 사용
```
Filesystem:read_file("/90-설정/템플릿-MOC.md")
```

### 2. 필수 요구사항
- **최소 3개 핵심개념** 포함 ✅
- **관련 MOC 연결** 🔶 권장
- **Dataview 쿼리** 포함
- **Mermaid 다이어그램** 포함

### 3. 저장 규칙
- 경로: `/30-연결/`
- 파일명: `맵-주제.md`

### 4. MOC 구조
```markdown
# 맵-주제

## 핵심 개념 (최소 3개)
- [[개념1]] - 설명
- [[개념2]] - 관계 명시
- [[개념3]] - 역할 설명

## 관련 MOC
- [[맵-상위주제]] (상위)
- [[맵-관련주제]] (관련)

## 구조도
\```mermaid
graph TD
    A[주제] --> B[개념1]
    A --> C[개념2]
    A --> D[개념3]
\```

## 자동 목록 (Dataview)
\```dataview
TABLE file.mtime as "수정일"
FROM [[]] 
WHERE contains(file.path, "핵심개념")
SORT file.mtime DESC
\```
```

### 5. 역링크 추가 프로세스
```python
for concept in registered_concepts:
    # 사용자 확인
    if confirm("개념에 MOC 역링크 추가?"):
        add_to_concept(concept, "[[맵-주제]]")
```

## 링크 규칙 (구조 연결)
- 핵심개념 → MOC (필수)
- MOC ↔ MOC (권장)
- 양방향 링크 선호

## 검증 체크리스트
- [ ] 핵심개념 3개 이상
- [ ] Dataview 쿼리 정상 작동
- [ ] Mermaid 다이어그램 포함
- [ ] 관련 MOC 연결 (권장)
- [ ] 역링크 완성도