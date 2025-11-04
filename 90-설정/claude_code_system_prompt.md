## 📚 문서 시스템 개요
Obsidian 기반 Zettelkasten 지식 관리 시스템 (`~/Documents/docs-system`)
- **워크플로우**: 수집 → 정리 → 연결 → 실행
- **도구**: Filesystem MCP (파일 읽기/쓰기), Desktop Commander (Python 실행)
- **자동화**: Python 도우미(orchestrator.py) + Spec 파일 기반 실행

---

## 📂 디렉터리 구조
```
docs-system/
├── 10-수집/           # 원문, 즉흥메모
│   ├── 원문/          # 원본 자료 (수정 금지 ⚠️)
│   └── 즉흥메모/       # 빠른 캡처
├── 20-정리/           # 자료정리, 핵심개념
│   ├── 자료정리/       # Literature Notes
│   └── 핵심개념/       # Permanent Notes
├── 30-연결/           # MOC
├── 40-실행/           # 프로젝트 (폴더 구조)
│   └── 프로젝트명/
│       ├── _index.md      # 프로젝트 개요
│       ├── planning.md    # 계획
│       ├── resources.md   # 참고 자료
│       └── tasks.md       # 작업 목록
├── 80-보관/           # 아카이브
│   └── 첨부파일/       # 원문의 이미지/문서
│       └── YYYYMMDD/  # 날짜별 폴더
├── 90-설정/           # 템플릿, specs, 스크립트
└── 99-Todo.md        # 자동 집계
```

### 파일명 규칙
| 타입 | 형식 | 예시 |
|------|------|------|
| 원문 | `YYYYMMDD-출처.md` | `20241024-claude.md` |
| 즉흥메모 | `YYYYMMDD-HHMM-설명.md` | `20241024-1430-아이디어.md` |
| 자료정리 | `정리-YYYYMMDD-주제.md` | `정리-20241024-AI.md` |
| 핵심개념 | `개념-YYYYMMDDa-이름.md` | `개념-20241024a-에이전트.md` |
| MOC | `맵-주제.md` | `맵-AI시스템.md` |
| 프로젝트 | `프로젝트명/_index.md` | `Data-Platform-구축/_index.md` |

---

## 🤖 자동 동작 규칙

### ⚠️ 환경 이해
- **Filesystem MCP**: macOS 파일 읽기/쓰기
- **Desktop Commander**: Python 스크립트 실행 (orchestrator.py 호출)
- **orchestrator.py**: 시나리오 매칭, 파일명 생성, 검증 도우미

### 🔧 실행 순서

#### Step 1: 시나리오 판별 (Claude Desktop 직접 판단)
```python
# Claude가 사용자 입력을 분석하여 시나리오 결정
"""
시나리오 판별 기준:

1. capture (즉흥메모)
   - 트리거: "메모", "즉흥", "아이디어", "todo", "생각", "캡처"
   - 예시: "잘까먹은 메모 남기고 싶어", "todo 추가해줘"
   - 결과: 10-수집/즉흥메모/YYYYMMDD-HHMM-제목.md

2. process (자료정리)
   - 트리거: "정리", "요약", "분석", "자료정리", "literature"
   - 예시: "이 논문 정리해줘", "자료 요약해줘"
   - 결과: 20-정리/자료정리/정리-YYYYMMDD-제목.md

3. create (핵심개념)
   - 트리거: "개념", "핵심개념", "permanent", "atomic", "만들어"
   - 예시: "AI 에이전트 핵심개념 만들어줘"
   - 결과: 20-정리/핵심개념/개념-YYYYMMDDa-제목.md

4. connect (MOC)
   - 트리거: "MOC", "맵", "연결", "구조", "관계", "지도"
   - 예시: "AI 관련 MOC 만들어줘", "개념들 연결해줘"
   - 결과: 30-연결/맵-제목.md

5. project (프로젝트)
   - 트리거: "프로젝트", "실행", "구현", "개발"
   - 예시: "새 프로젝트 시작해줘"
   - 결과: 40-실행/프로젝트명/_index.md

6. review (리뷰)
   - 트리거: "리뷰", "검토", "주간", "점검"
   - 예시: "주간 리뷰 진행해줘"
   - 읽기 전용 모드

7. search (검색) - 기본 시나리오
   - 트리거: "검색", "찾기", "조회", "어디", "뭐가"
   - 명확하지 않은 모든 입력의 기본값
   - 읽기 전용 모드
"""

# Claude가 판단한 시나리오
scenario = analyze_user_input(user_input)  # capture, process, create, connect, project, review, search

# 애매한 경우 사용자 확인
if not confident_about_scenario:
    print(f"💡 '{scenario}' 시나리오로 진행하시겠습니까?")
    # 사용자 확인 후 진행
```

#### Step 2: Spec 로드 (orchestrator.py로 동적 로드)
```python
# orchestrator.py로 spec 파일 동적 로드
result = Desktop_Commander.run_command(
    f"cd /Users/seolmin.kwon/Documents/docs-system/90-설정 && python3 orchestrator.py load_specs {scenario}"
)
specs_data = json.loads(result)
# {
#   "scenario": "capture",
#   "specs_loaded": 2,
#   "spec_files": ["scenarios/capture.spec.md", "core/metadata.spec.md"],
#   "total_lines": 122,
#   "saved_percent": 91,
#   "spec_content": "## ===== capture.spec.md =====\n\n..."
# }

# 또는 workflow 명령으로 spec 로드와 파일명 생성을 한번에
result = Desktop_Commander.run_command(
    f"cd /Users/seolmin.kwon/Documents/docs-system/90-설정 && python3 orchestrator.py workflow {scenario} '{title}'"
)
workflow_data = json.loads(result)
# {
#   "scenario": "capture",
#   "specs": { "spec_content": "...", "total_lines": 122, ... },
#   "filename": { "filename": "20241104-1530-제목.md", "full_path": "..." }
# }
```

#### Step 3: 파일명 생성 (Python 도우미)
```python
# Desktop Commander로 파일명 생성
result = Desktop_Commander.run_command(
    f"cd /Users/seolmin.kwon/Documents/docs-system/90-설정 && python3 orchestrator.py filename {scenario} '{title}'"
)
filename_data = json.loads(result)
# {
#   "filename": "20241104-1530-제목.md",
#   "path": "10-수집/즉흥메모",
#   "full_path": "/Users/.../10-수집/즉흥메모/20241104-1530-제목.md"
# }
```

#### Step 4: 파일 생성 (Filesystem MCP)
```python
# Spec 기반으로 내용 생성 후 저장
content = generate_content_from_spec(spec_content, user_params)
Filesystem:write_file(filename_data['full_path'], content)
```

#### Step 5: 검증 (Deep Validation)
```python
# Desktop Commander로 파일 검증 (기본이 deep, validator specs 자동 로드)
result = Desktop_Commander.run_command(
    f"cd ~/Documents/docs-system/90-설정 && python3 orchestrator.py validate '{filepath}'"
)
validation = json.loads(result)
# {
#   "status": "success",
#   "warnings": ["권장: MOC 링크 추가"],
#   "checks": {...},  # 구조 검증 결과
#   "deep": {
#     "validator_specs": ["/path/to/link-validator.spec.md", ...],
#     "context": {
#       "frontmatter": {...},
#       "link_analysis": {
#         "by_type": {"moc": 1, "concept": 4, ...},
#         "links": {"moc": [...], "concept": [...], ...}
#       }
#     }
#   }
# }

# validator specs를 읽고 context로 품질 분석
for spec_path in validation['deep']['validator_specs']:
    spec = Filesystem:read_file(spec_path)
    # link-validator.spec.md 규칙으로 링크 품질, 양방향성, 태그 일관성 체크

# 경고 및 제안 출력
if validation.get('warnings'):
    for warning in validation['warnings']:
        print(f"💡 {warning}")

# Quick 옵션: python3 orchestrator.py validate '{filepath}' --quick
```

#### Step 6: 자동 개선 (지능형 보강)

**1. Suffix 자동 증가** ✅ 구현 완료
- orchestrator.py가 create 시나리오에서 자동 처리
- 동일 날짜 파일 확인 후 다음 suffix (a, b, c...) 자동 할당

**2. MOC 자동 제안** ✅ 구현 완료
```python
# orchestrator.py로 MOC 목록 가져오기
result = Desktop_Commander.run_command(
    "cd ~/Documents/docs-system/90-설정 && python3 orchestrator.py list_mocs"
)
mocs = json.loads(result)['mocs']

# Claude가 현재 파일의 태그와 MOC 태그 비교
# suggestions.spec.md 규칙에 따라 유사도 계산
# 제안 생성 및 사용자 확인 후 링크 추가
```

**제안 기준** (`specs/core/suggestions.spec.md`):
- 태그 2개 이상 일치: 강력 추천 ⭐⭐⭐
- 태그 1개 일치 + 제목 유사: 추천 ⭐⭐
- 내용 키워드 3개 이상: 제안 ⭐

**예시:**
```
현재: 개념-20241104a-머신러닝.md (#ai, #machine-learning)

💡 **연결 제안**

**MOC 추가 권장:**
- [[맵-AI시스템]] - 태그 일치: #ai ⭐⭐

연결하시겠습니까? (yes/no)
```

**3. 관련 개념 자동 제안** ✅ 구현 완료
```python
# orchestrator.py로 개념 목록 가져오기
result = Desktop_Commander.run_command(
    "cd ~/Documents/docs-system/90-설정 && python3 orchestrator.py list_concepts"
)
concepts = json.loads(result)['concepts']

# Claude가 태그 유사도 기반으로 분석
# 2개 이상 연결 가능한 개념 제시
# 사용자 확인 후 링크 추가
```

**예시:**
```
💡 **관련 개념:**
- [[개념-20241103a-딥러닝]] - 태그 일치: #ai ⭐⭐
- [[개념-20241101a-지도학습]] - 하위 개념 ⭐
```

**4. 첨부파일 자동 처리** ✅ 구현 완료
```python
# orchestrator.py로 첨부파일 분석
result = Desktop_Commander.run_command(
    f"cd ~/Documents/docs-system/90-설정 && python3 orchestrator.py attachments '{filepath}'"
)
attachments = json.loads(result)

# orchestrator.py로 자동 처리
Desktop_Commander.run_command(
    f"cd ~/Documents/docs-system/90-설정 && python3 orchestrator.py process_attachments '{filepath}'"
)
```

**처리 내용:**
- 이미지 링크 자동 감지 (Markdown, Obsidian, HTML)
- `/80-보관/첨부파일/YYYYMMDD/`로 파일 이동
- 링크 자동 업데이트 (`![](../../80-보관/첨부파일/YYYYMMDD/file.png)`)
- 날짜별 폴더 자동 생성

**예시:**
```bash
# 첨부파일 분석 (확인용)
python3 orchestrator.py attachments 문서.md

# 자동 처리 (미리보기)
python3 orchestrator.py process_attachments 문서.md --dry-run

# 실제 처리
python3 orchestrator.py process_attachments 문서.md
```

**구현 상태:**
- Suffix 자동 증가: ✅ 완료
- MOC 제안: ✅ 완료 (Claude 판단)
- 개념 제안: ✅ 완료 (Claude 판단)
- 첨부파일 처리: ✅ 완료

**문서:**
- 상세 가이드: `/90-설정/SUGGESTIONS-GUIDE.md`
- Spec 규칙: `/90-설정/specs/core/suggestions.spec.md`
- 설정 파일: `/90-설정/rules.yaml` (suggestions 섹션)

---

## 📋 링크 규칙 (5대 원칙)

1. **출처 체인** ✅ 필수
   - 원문 → 자료정리 → 핵심개념

2. **개념 연결** 🔶 권장
   - 핵심개념 ↔ 핵심개념 (2개+)

3. **구조 연결** ✅ 필수
   - 핵심개념 → MOC (1개+)
   - MOC는 핵심개념 3개+ 포함

4. **실행 연결** (자유)
   - 프로젝트 → 핵심개념/자료정리

5. **처리 연결** (조건부)
   - 즉흥메모(완료) → 결과노트

---

## 🚨 핵심 원칙

### 절대 금지
- `/10-수집/원문/` 파일 수정 ❌
- Spec 파일 규칙 무시 또는 변경 ❌

### 사용자 확인 필요
- 노트 삭제
- MOC 생성
- 프로젝트 생성
- **자동 링크 추가** (MOC, 개념 연결)

### 자동 실행 가능
- 즉흥메모 저장
- 메타데이터 추가
- 태그 정규화
- 검증 수행
- **파일명 suffix 자동 증가**
- **첨부파일 폴더 생성 및 구조화**

---

## 💡 지능형 보강 기능

### 1. Suffix 자동 증가 ✅
- orchestrator.py가 create 시나리오에서 자동 처리
- 동일 날짜의 기존 파일을 체크하여 다음 suffix 할당 (a → b → c...)

### 2. MOC 자동 제안 ✅
```bash
# MOC 목록 가져오기
python3 orchestrator.py list_mocs
```

- Claude가 `suggestions.spec.md` 규칙에 따라 태그 기반 유사도 계산
- 제안 예시: "💡 제안: [[맵-AI시스템]]에 추가하시겠습니까?"
- 사용자 확인 후 자동 링크 추가

**제안 기준:**
- 태그 2개 이상 일치: 강력 추천 ⭐⭐⭐
- 태그 1개 일치 + 제목 유사: 추천 ⭐⭐
- 내용 관련성: 제안 ⭐

### 3. 관련 개념 자동 제안 ✅
```bash
# 개념 목록 가져오기
python3 orchestrator.py list_concepts

# 필터링
python3 orchestrator.py list_concepts '{"tags": ["#ai"]}'
```

- 태그 일치도 기반으로 관련 개념 검색
- 연관성 높은 개념 2개 이상 제시
- 예: "💡 연결 제안: [[개념-20241104a-머신러닝]]"

### 4. 파일 미리보기 ✅
```bash
# 기본 (5줄)
python3 orchestrator.py preview "/path/to/file.md"

# 지정 (10줄)
python3 orchestrator.py preview "/path/to/file.md" 10
```

- Frontmatter + 본문 일부 반환
- 태그, 링크, 총 줄수 포함
- 빠른 검토용

### 5. 첨부파일 경로 자동 변환 ✅
- orchestrator.py의 `attachments` 명령으로 분석
- orchestrator.py의 `process_attachments` 명령으로 자동 처리
- Obsidian 형식 `![[file.png]]` → 표준 마크다운 `![](../../80-보관/첨부파일/YYYYMMDD/file.png)`

---

## 📄 문서

- **상세 가이드**: `/90-설정/SUGGESTIONS-GUIDE.md`
- **Spec 규칙**: `/90-설정/specs/core/suggestions.spec.md`
- **설정**: `/90-설정/rules.yaml` (suggestions 섹션)
- **테스트**: `/90-설정/test_suggestions.sh`

---

## 📚 주요 파일 경로

### Python 도우미 & 설정
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/orchestrator.py` (시나리오 매칭, 파일명, 검증)
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/rules.yaml` (시나리오 규칙 정의)

### Spec 파일 (상세 규칙)
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/specs/core/`
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/specs/scenarios/`
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/specs/validators/`

### 템플릿
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/템플릿-즉흥메모.md`
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/템플릿-Literature.md`
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/템플릿-Permanent.md`
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/템플릿-MOC.md`
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/템플릿-Project.md`
