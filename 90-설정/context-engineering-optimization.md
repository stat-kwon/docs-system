# Context Engineering 최적화 방안

**작성일**: 2024-11-05  
**목적**: Process 시나리오 중복 제거 + Context 효율 유지

---

## 🎯 핵심 원칙

### 1. 분산 구조 유지 (Context 선택적 로드)
- ✅ Spec 파일 분리 → 필요한 것만 로드
- ✅ orchestrator.py 분리 → Claude context 보호
- ✅ 템플릿 유지 → 구조 사고 비용 감소

### 2. 중복 제거 (Context 낭비 방지)
- ❌ 동일 정보 다중 정의
- ✅ SSOT (Single Source of Truth) 확립
- ✅ 참조 체계 명확화

### 3. 일괄 로드 패턴 활용
- ✅ workflow 명령으로 필요한 모든 정보 한번에
- ❌ 왕복 최소화 (4회 → 1회)

---

## 📊 Context 효율 분석

### 현재 상태: "정리해줘" 실행 시

```
System Prompt: 191줄 (상세 규칙 포함)
  → 트리거 키워드, 파일명 예시, 메타데이터 상세 등 중복

orchestrator.py 호출:
  1. load_specs("process")
     → process.spec.md: 150줄
     → metadata.spec.md: 80줄
  2. filename("process", "제목")
  3. validate(filepath)

총 Context: 약 471줄
왕복 횟수: 4회
중복 정보: 약 40-50줄 (파일명, 경로, 필수 필드 등)
```

### 최적화 목표

```
System Prompt: 90줄 (워크플로우 + 참조)
  → 구체적 규칙은 spec 참조로 대체

orchestrator.py 호출:
  1. workflow("process", "제목")
     → specs + filename + validation_rules 한번에

총 Context: 약 270줄
왕복 횟수: 1회
중복 제거: SSOT 확립
```

**개선 효과**:
- Context: **43% 감소** (471 → 270줄)
- 왕복: **75% 감소** (4회 → 1회)
- 중복: **제거** (SSOT)

---

## 🔧 구체적 수정 사항

### 1. System Prompt 간소화 (191줄 → 90줄)

#### 삭제할 내용:
```markdown
❌ 시나리오별 트리거 키워드 상세
   - "정리", "요약", "분석"... → process.spec.md로 이동

❌ 파일명 규칙 예시
   - "정리-YYYYMMDD-주제.md" → structure.spec.md 참조

❌ 메타데이터 필드 상세
   - type, source, created... → metadata.spec.md 참조

❌ 링크 규칙 5대 원칙 상세
   - 출처 체인, 개념 연결... → link-rules.spec.md 참조

❌ 폴더 구조 트리
   - 디렉토리 계층... → structure.spec.md 참조
```

#### 유지할 내용:
```markdown
✅ 워크플로우 개념 (수집→정리→연결→실행)

✅ 도구 사용 원칙
   - Filesystem MCP: 파일 시스템만
   - Desktop Commander: 실행만
   - Claude: 판단 + 생성

✅ 실행 순서 (6단계 절차 개요)
   Step 1: 시나리오 판별 (Claude)
   Step 2: Spec 로드 (workflow 명령)
   Step 3-6: ...

✅ SSOT 참조 테이블
   | 규칙 | 파일 |
   |------|------|
   | 메타데이터 | metadata.spec.md |
   | 파일명/구조 | structure.spec.md |
   | 링크 규칙 | link-rules.spec.md |
```

---

### 2. 메타데이터 필드 최소화 (6개 → 3개)

#### Context 가치 분석:

| 필드 | Context 비용 | 실제 사용도 | 검색/필터 가치 | 판정 |
|------|-------------|-----------|--------------|------|
| `source` | 3줄 | **높음** (출처 체인 필수) | **높음** | ✅ 필수 |
| `created` | 2줄 | **높음** (시간 추적) | **높음** | ✅ 필수 |
| `tags` | 3줄 | **높음** (연결/검색) | **높음** | ✅ 필수 |
| `type` | 3줄 | 낮음 (경로로 유추 가능) | 중간 | ⚠️ 선택 |
| `updated` | 2줄 | 낮음 (자동 업데이트 미구현) | 중간 | ❌ 삭제 |
| `status` | 2줄 | **낮음** (대부분 방치) | 낮음 | ❌ 삭제 |

#### 수정 전 (15줄 비용):
```yaml
---
type: literature
source: [[원문]]
created: 2024-11-05
updated: 2024-11-05
tags: []
status: unprocessed
---
```

#### 수정 후 (9줄 비용):
```yaml
---
source: [[원문]]
created: 2024-11-05
tags: []
---
```

**효과**: Context **40% 절약** (15줄 → 9줄)

---

### 3. Spec 파일 SSOT 확립

#### Process 시나리오 예시:

**Before (중복 존재)**:
```
System Prompt:
  - "파일명: 정리-YYYYMMDD-주제.md"
  - "경로: 20-정리/자료정리"

process.spec.md:
  - "파일명: 정리-YYYYMMDD-주제.md"  # 중복
  - "저장 경로: /20-정리/자료정리/"    # 중복

structure.spec.md:
  - "| 자료정리 | 정리-YYYYMMDD-주제.md | ..."  # 중복
```

**After (SSOT)**:
```
System Prompt:
  - "파일명 규칙: structure.spec.md 참조"

process.spec.md:
  ## 파일 생성
  - 파일명: `structure.spec.md` 참조
  - 경로: `rules.yaml` 참조

structure.spec.md (SSOT):
  ## 파일명 규칙
  | 노트 타입 | 형식 | 예시 |
  |----------|------|------|
  | 자료정리 | `정리-YYYYMMDD-주제.md` | `정리-20241024-AI.md` |
```

---

### 4. workflow 명령 적극 활용

#### 현재 (4회 왕복):
```python
# Step 1: Claude 판단
scenario = "process"

# Step 2: Spec 로드
result = orchestrator.py load_specs(scenario)
specs = parse(result)

# Step 3: 파일명 생성
result = orchestrator.py filename(scenario, title)
filename = parse(result)

# Step 4: (파일 생성)

# Step 5: 검증
result = orchestrator.py validate(filepath)
```

#### 최적화 (1회 호출):
```python
# Step 1: Claude 판단
scenario = "process"

# Step 2: workflow 한번에
result = orchestrator.py workflow(scenario, title)
# → 반환:
# {
#   "scenario": "process",
#   "specs": {
#     "spec_content": "...",
#     "total_lines": 230
#   },
#   "filename": {
#     "filename": "정리-20241105-제목.md",
#     "full_path": "/Users/.../20-정리/자료정리/정리-20241105-제목.md"
#   }
# }

# Step 3-4: Claude가 specs 기반 파일 생성

# Step 5: 검증 (별도 호출)
result = orchestrator.py validate(filepath)
```

**효과**: 
- 왕복 **50% 감소** (4회 → 2회)
- Claude 사고 과정 간소화

---

## 📋 액션 플랜

### Phase 1: 메타데이터 최소화 (즉시)

#### 1-1. metadata.spec.md 수정
```markdown
## 타입별 필수 필드 (최소)

| 타입 | 필수 필드 | 선택 필드 |
|------|----------|----------|
| literature | source, created, tags | - |
| permanent | source, created, tags | - |
| moc | created, tags | - |

## 삭제된 필드
- `type`: 파일 경로로 유추 가능
- `status`: 실제 사용도 낮음
- `updated`: 자동 업데이트 미구현 시 불필요
```

#### 1-2. 템플릿-Literature.md 수정
```yaml
# Before (6개 필드)
---
id: {{title}}
title: "{{title}}"
source: [[원문 링크]]
author: 
created: {{date:YYYY-MM-DD}}
updated: {{date:YYYY-MM-DD}}
type: literature
tags: []
status: unprocessed
---

# After (3개 필드)
---
source: [[원문 링크]]
created: {{date:YYYY-MM-DD}}
tags: []
---
```

---

### Phase 2: SSOT 확립 및 중복 제거 (1주)

#### 2-1. System Prompt 간소화

**삭제**:
- 모든 시나리오별 트리거 키워드 목록
- 파일명 형식 예시
- 메타데이터 필드 상세
- 링크 규칙 5대 원칙 상세
- 폴더 구조 전체 트리

**추가**:
```markdown
## SSOT 참조 테이블

| 규칙 타입 | 파일 | 용도 |
|----------|------|------|
| 시나리오 트리거 | `specs/scenarios/*.spec.md` | 감지 기준 |
| 메타데이터 | `specs/core/metadata.spec.md` | 필드 정의 |
| 파일명/구조 | `specs/core/structure.spec.md` | 명명 규칙 |
| 링크 정책 | `specs/core/link-rules.spec.md` | 연결 원칙 |
| 자동 설정 | `rules.yaml` | 경로/템플릿 |
```

#### 2-2. process.spec.md 수정

**삭제**:
```markdown
❌ ### 2. 필수 YAML 필드
```yaml
---
type: literature
source: [[YYYYMMDD-출처]]  # ✅ 필수
created: YYYY-MM-DD
tags: [literature/topic]
---
```
```

**수정 후**:
```markdown
✅ ### 2. 메타데이터
- 필수 필드: `metadata.spec.md` 참조
- process 고유 규칙:
  - `source`는 반드시 원문 파일 (10-수집/원문/)
  - `tags`는 `#literature/주제` 계층 구조
```

#### 2-3. 기타 spec 파일 동일 작업
- create.spec.md
- capture.spec.md
- connect.spec.md
- project.spec.md

---

### Phase 3: workflow 명령 활용 강화 (2주)

#### 3-1. System Prompt 수정

```markdown
### Step 2: Spec 로드 및 파일명 생성 (한번에)

```python
# workflow 명령으로 필요한 모든 정보 획득
result = Desktop_Commander.run_command(
    f"cd ~/Documents/docs-system/90-설정 && python3 orchestrator.py workflow {scenario} '{title}'"
)

workflow_data = json.loads(result)
# {
#   "scenario": "process",
#   "specs": {
#     "spec_content": "...",  # 로드된 모든 spec
#     "total_lines": 230
#   },
#   "filename": {
#     "filename": "정리-20241105-제목.md",
#     "full_path": "..."
#   }
# }

# Claude는 specs 내용을 기반으로 파일 생성
# filename은 그대로 사용
```
```

#### 3-2. orchestrator.py 검증 (이미 구현됨)
```python
def workflow(scenario: str, title: str) -> dict:
    """Spec 로드 + 파일명 생성을 한번에"""
    specs = load_specs(scenario)
    filename_info = filename(scenario, title)
    
    return {
        "scenario": scenario,
        "specs": specs,
        "filename": filename_info
    }
```

---

## 📊 예상 효과

### Context 효율

| 항목 | Before | After | 개선 |
|------|--------|-------|------|
| System Prompt | 191줄 | 90줄 | **53% 감소** |
| 메타데이터 비용 | 15줄 | 9줄 | **40% 감소** |
| 중복 정보 | 40-50줄 | 0줄 | **제거** |
| 총 Context | 471줄 | 270줄 | **43% 감소** |
| 왕복 횟수 | 4회 | 2회 | **50% 감소** |

### 유지보수

| 항목 | Before | After |
|------|--------|-------|
| 파일명 규칙 변경 | 4곳 수정 | 1곳 수정 (structure.spec) |
| 메타데이터 추가 | 3곳 수정 | 1곳 수정 (metadata.spec) |
| 링크 정책 변경 | 3곳 수정 | 1곳 수정 (link-rules.spec) |

---

## ✅ 유지되는 핵심 가치

### 1. Context 선택적 로드 ✅
```
capture 실행 → capture.spec만 로드 (150줄)
process 실행 → process.spec + metadata.spec (230줄)
create 실행 → create.spec + metadata.spec + link-rules.spec (380줄)
```

### 2. Claude Context 보호 ✅
```
복잡한 로직 → orchestrator.py
  - 파일명 생성 (날짜, suffix 계산)
  - 경로 검증
  - 파일 스캔

Claude는 판단과 생성에만 집중
```

### 3. 템플릿 효율 ✅
```
템플릿 로드 (50줄) → 변수 치환 → 완성
vs
매번 구조 사고 (100줄)
```

### 4. 분산 구조 확장성 ✅
```
새 시나리오 추가:
  1. scenarios/new.spec.md 작성
  2. rules.yaml에 등록
  3. 기존 spec 영향 없음
```

---

## 🎯 최종 결론

### 삭제하지 말아야 할 것:
1. ✅ Spec 파일 분리 구조 (Context 효율의 핵심)
2. ✅ orchestrator.py 역할 (Claude context 보호)
3. ✅ 템플릿 파일 (사고 비용 감소)
4. ✅ workflow 명령 (일괄 로드)

### 개선해야 할 것:
1. 🔧 중복 정보 제거 (SSOT 확립)
2. 🔧 System Prompt 간소화 (50% 축소)
3. 🔧 메타데이터 최소화 (6→3 필드)
4. 🔧 workflow 명령 활용 강화

### 핵심 철학:
> **"분산 구조 유지 (Context 효율) + 중복 제거 (유지보수 편의)"**

---

## 📝 다음 단계

1. [ ] Phase 1 착수 (메타데이터 최소화)
2. [ ] Phase 2 진행 (SSOT 확립)
3. [ ] Phase 3 완료 (workflow 활용)
4. [ ] 전체 시나리오 동일 작업 확대

**예상 소요 시간**: 3-4주 (점진적 개선)
