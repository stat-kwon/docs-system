## 📚 문서 시스템 개요
Obsidian 기반 Zettelkasten 지식 관리 시스템 (`~/Documents/docs-system`)
- **워크플로우**: 수집 → 정리 → 연결 → 실행
- **도구**: Filesystem MCP (macOS 파일 접근)
- **자동화**: Shell 스크립트 로직 100% 준수

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
- **bash_tool**: Linux 컨테이너 (macOS `/Users/...` 경로 접근 불가)
- **Filesystem MCP**: macOS 파일 읽기/쓰기 전용
- **Shell 스크립트**: 실행 불가, **로직 100% 엄격 준수**

### 🔧 실행 순서

#### Step 1: 키워드 매칭 (Claude 판단)
```python
# loader.sh의 identify_scenario() 키워드 패턴 참조
loader = Filesystem:read_file("/Users/seolmin.kwon/Documents/docs-system/90-설정/loader.sh")

# 7가지 시나리오: capture, process, create, connect, project, review, search
scenario = claude_match_scenario(user_input)
```

#### Step 2: Spec 로드
```python
# loader.sh의 load_specs_for_scenario() case문 확인
# 시나리오별 spec 파일 목록 결정 후 로드
for spec in spec_files[scenario]:
    Filesystem:read_file(f"/Users/seolmin.kwon/Documents/docs-system/90-설정/specs/{spec}")
```

#### Step 3: 파일 생성
```python
# orchestrator.sh의 해당 함수 로직 100% 준수
orchestrator = Filesystem:read_file("/Users/seolmin.kwon/Documents/docs-system/90-설정/orchestrator.sh")

# 시나리오별 함수: capture(), process(), extract(), connect(), project() 등
# - 파일명 생성 규칙
# - YAML frontmatter 구조
# - 본문 템플릿

Filesystem:write_file(filename, content)
```

#### Step 3.5: 자동 개선 (지능형 보강)
```python
# 0. 첨부파일 처리 (원문 저장 시)
attachments = re.findall(r'!\[\[(.+?)\]\]', content)
if attachments:
    # 첨부파일 저장 폴더 생성
    attachment_dir = f"/80-보관/첨부파일/{date}/"
    Filesystem:create_directory(attachment_dir)
    
    # YAML에 attachments 필드 추가
    yaml_data['attachments'] = attachments
    
    # 자료정리 생성 시 경로 변환
    # ![[file.png]] → ![](../../80-보관/첨부파일/YYYYMMDD/file.png)

# 1. 동일 날짜 파일 체크 (suffix 자동 증가)
existing_files = Filesystem:list_directory("/20-정리/핵심개념/")
if f"개념-{date}a-{concept}.md" exists:
    suffix = "b"  # a → b → c 자동 증가

# 2. MOC 자동 검색 및 제안
moc_files = Filesystem:list_directory("/30-연결/")
related_mocs = search_by_tags_or_keywords(moc_files, concept)
# → "[[맵-AI시스템]]에 추가하시겠습니까?"

# 3. 관련 개념 자동 검색
concept_files = Filesystem:list_directory("/20-정리/핵심개념/")
related_concepts = search_by_tags(concept_files, tags)
# → "[[개념-A]], [[개념-B]]와 연결하시겠습니까?"

# 4. 제안된 링크로 파일 업데이트 (사용자 확인 후)
if user_confirms:
    Filesystem:edit_file(filename, edits)
```

#### Step 4: 검증
```python
# validate.sh의 검증 로직 확인 및 수행
validator = Filesystem:read_file("/Users/seolmin.kwon/Documents/docs-system/90-설정/validate.sh")

# 필수 검증: source 필드, MOC 연결 등
# 권장 검증: 개념 연결 2개+
```

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
- Shell 스크립트 로직 무시 또는 변경 ❌

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

### 1. Suffix 자동 증가
```python
# orchestrator.sh의 TODO 구현
existing = Filesystem:list_directory("/20-정리/핵심개념/")
suffixes = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
for s in suffixes:
    if f"개념-{date}{s}-{concept}.md" not in existing:
        suffix = s
        break
```

### 2. 첨부파일 경로 자동 변환
```python
# 자료정리 생성 시 원문의 첨부파일 참조 변환
if source_attachments:
    for attachment in source_attachments:
        # Obsidian 형식을 표준 마크다운으로 변환
        old_ref = f"![[{attachment}]]"
        new_ref = f"![](../../80-보관/첨부파일/{date}/{attachment})"
        content = content.replace(old_ref, new_ref)
```

### 3. MOC 자동 제안
```python
# 태그 또는 키워드 기반 검색
moc_list = Filesystem:list_directory("/30-연결/")
for moc_file in moc_list:
    moc_content = Filesystem:read_file(moc_file)
    if concept_tag in moc_content or keyword_match:
        print(f"💡 제안: [[{moc_name}]]에 추가하시겠습니까?")
```

### 4. 관련 개념 자동 제안
```python
# 태그 일치도 기반 검색
concept_list = Filesystem:list_directory("/20-정리/핵심개념/")
related = []
for concept_file in concept_list:
    concept_content = Filesystem:read_file(concept_file)
    if tag_overlap_score(tags, concept_tags) > threshold:
        related.append(concept_name)

if len(related) >= 2:
    print(f"💡 제안: {related[0]}, {related[1]}와 연결하시겠습니까?")
```

---

## 📁 주요 파일 경로

### Shell 스크립트 (로직 참조)
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/loader.sh`
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/orchestrator.sh`
- `/Users/seolmin.kwon/Documents/docs-system/90-설정/validate.sh`

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

---

**모든 상세 로직(키워드, 파일명 생성, 검증 기준 등)은 shell 스크립트와 spec 파일에서 확인하세요.**
