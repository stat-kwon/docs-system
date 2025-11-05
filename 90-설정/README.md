# Zettelkasten 자동화 시스템

> Obsidian 기반 지식관리 시스템을 위한 워크플로 오케스트레이터

## 📌 한눈에 보기
- ⚙️ **모듈형 서비스 아키텍처**: 설정 로딩, 스펙 번들링, 파일명 생성, 템플릿 조회, 첨부파일 처리를 각각의 서비스가 담당합니다.
- 🧩 **SSOT 중심 설계**: 모든 규칙은 `rules.yaml`과 `specs/` 디렉터리에 집중되어 있으며, 템플릿과 검증 규칙도 단일 출처로 관리됩니다.
- 📉 **컨텍스트 예산 관리**: 시나리오마다 로드된 스펙/밸리데이터의 라인 수를 집계해 LLM 프롬프트 길이를 통제합니다.
- 🧾 **풍부한 메타데이터**: 템플릿과 스펙이 확장된 frontmatter 필드를 공유해 검색성 높은 노트를 생성합니다.

## 디렉터리 개요
```
90-설정/
├─ README.md                     # 현재 문서
├─ claude_code_system_prompt.md  # Claude용 시스템 가이드
├─ context-engineering-optimization.md
├─ orchestrator.py               # CLI 진입점 (workflow, process-attachments)
├─ orchestrator/                 # 서비스 모듈 집합
│  ├─ __init__.py                # 서비스 팩토리
│  ├─ attachment_service.py      # 첨부파일 이동 및 링크 업데이트
│  ├─ config_loader.py           # rules.yaml + docs_root 해석
│  ├─ context_budget.py          # 컨텍스트 사용량 요약
│  ├─ filename_service.py        # 시나리오별 파일명 생성
│  ├─ logging_config.py          # 로거 설정
│  ├─ spec_loader.py             # 스펙/밸리데이터 로딩
│  ├─ template_service.py        # 템플릿 메타데이터 설명
│  └─ workflow_service.py        # 서비스 조합 및 최종 응답 생성
├─ rules.yaml                    # 시나리오/템플릿/검증 규칙의 SSOT
├─ specs/                        # core 규칙 + 시나리오 스펙 + validator 번들
└─ 템플릿-*.md                    # 노트 생성용 frontmatter 템플릿
```

## 아키텍처 흐름
```
┌─────────────────────────┐
│ Claude Desktop (사용자 입력) │
└─────────────┬──────────┘
              ▼
┌─────────────────────────┐
│ orchestrator.py (CLI)   │  argparse → build_services()
└─────────────┬──────────┘
              ▼
┌─────────────────────────┐      ┌────────────────────────────┐
│ WorkflowService         │◀────▶│ SpecLoader / TemplateSvc   │
│ - 시나리오 확인          │      │ - spec / validator 번들링   │
│ - 컨텍스트 예산 보고      │      │ - 템플릿 frontmatter 설명    │
│ - 파일명 생성 위임        │      └────────────────────────────┘
│ - 검증 규칙/자동 실행 상태│
└─────────────┬──────────┘
              ▼
┌─────────────────────────┐
│ AttachmentService       │ (process-attachments 전용)
└─────────────────────────┘
```

## 핵심 구성 요소
### orchestrator.py
- `workflow`와 `process-attachments` 두 개의 서브커맨드를 제공하는 얇은 CLI 레이어입니다.
- 실행 시 `build_services()`를 통해 모든 서비스 인스턴스를 구성하고 JSON 응답을 반환합니다.

### orchestrator 패키지
| 모듈 | 역할 |
| --- | --- |
| `config_loader.ConfigLoader` | `rules.yaml`을 읽고 `docs_root`, 컨텍스트 목표치를 계산합니다. 환경 변수 `DOCS_HOME`이 우선합니다. |
| `spec_loader.SpecLoader` | 시나리오별로 정의된 spec/validator 파일을 로드하고 원문과 라인 수를 제공해 컨텍스트 예산을 계산합니다. |
| `filename_service.FilenameService` | 슬러그 정규화, 접두사/폴더 계산, 중복 방지용 시퀀스 처리를 담당합니다. |
| `template_service.TemplateService` | 템플릿 파일의 frontmatter 필드를 파싱해 LLM이 사용할 설명을 제공합니다. |
| `workflow_service.WorkflowService` | 위 서비스들을 조합해 단일 호출로 필요한 정보(스펙, 템플릿, 파일명, 검증 규칙, 컨텍스트 라인)를 돌려줍니다. |
| `attachment_service.AttachmentService` | 노트에 첨부된 리소스를 표준 위치로 이동시키고 링크를 업데이트합니다. |
| `context_budget.summarize` | 로드된 spec/validator의 총 라인 수를 계산하여 목표(기본 270줄) 대비 현황을 보고합니다. |

### rules.yaml
- `scenarios.<name>` 아래에 템플릿, 스펙 번들, 검증 규칙, 자동 실행 여부 등이 정의됩니다.
- `context.target_total_lines`로 워크플로 호출 시 목표 컨텍스트 길이를 관리합니다.
- 새로운 시나리오는 이 파일 하나만 수정하면 나머지 서비스가 자동으로 반영합니다.

### specs/
- `core/`: 구조, 메타데이터, 링크, 템플릿 사용 지침 등 전역 규칙을 정의합니다.
- `scenarios/`: 시나리오별 체크리스트와 필요한 include 목록을 담습니다.
- `validators/`: 링크/우선순위 검증 등 후속 점검 시 참고할 규칙입니다.

### 템플릿
- `템플릿-*.md` 파일은 frontmatter와 본문 구조를 제공하며, `TemplateService`가 필수/선택 필드를 JSON으로 설명합니다.
- 템플릿만 수정하면 워크플로 응답 및 검증 규칙에 동일하게 반영되어 SSOT를 유지합니다.

## CLI 사용법
```bash
# 시나리오 전체 워크플로 (spec 번들 + 컨텍스트 보고 + 템플릿 + 파일명)
python3 orchestrator.py workflow <scenario> [title] [--set key=value ...]

# 첨부파일 이동 및 링크 패치
python3 orchestrator.py process-attachments <markdown-path> [--dry-run]
```

### 예시
```bash
$ python3 orchestrator.py workflow create "에이전트 설계"
{
  "scenario": "create",
  "specs": { ... },
  "template": {
    "path": "90-설정/템플릿-Permanent.md",
    "frontmatter": {"title": "", "aliases": [], ...}
  },
  "filename": {
    "path": "20-정리/핵심개념/개념-20241104a-에이전트설계.md",
    "slug": "에이전트설계",
    "sequence": "a"
  },
  "context_lines": {"total": 188, "target": 270, ...}
}
```

```bash
$ python3 orchestrator.py process-attachments "20-정리/핵심개념/개념-20241104a-에이전트설계.md" --dry-run
{
  "moved": [],
  "links_updated": [],
  "notes": "No attachments found"
}
```

## 개발 팁
- **환경 변수**: `DOCS_HOME`을 지정하면 다른 워크스페이스에서도 동일 설정으로 실행할 수 있습니다.
- **의존성**: 표준 라이브러리 외 별도 패키지를 사용하지 않습니다.
- **테스트**: `python3 -m compileall 90-설정/orchestrator.py 90-설정/orchestrator` 명령으로 기본 구문 검사를 수행합니다.

---
이 README는 최신 워크플로 통합 구조와 SSOT 전략을 반영하도록 갱신되었습니다.
