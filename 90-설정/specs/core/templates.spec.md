# 템플릿 사용 Spec

## 목적
- 모든 노트 구조와 메타데이터는 `/90-설정` 루트에 있는 템플릿 파일을 단일 진실 공급원(SSOT)으로 삼는다.
- 시나리오에서 문서 구조를 수정하려면 템플릿만 업데이트하고, 개별 Spec은 템플릿 경로만 참조한다.

## 공통 사용 절차
1. `Filesystem:read_file("/90-설정/{{template_filename}}")`로 템플릿을 로드한다.
2. 프론트매터와 본문 섹션을 그대로 사용하고, 주석(`<!-- -->`)으로 표시된 지침에 맞춰 내용을 채운다.
3. 템플릿에 정의된 메타데이터 필드는 모두 유지하며, 값만 채우거나 필요 시 배열에 항목을 추가한다.
4. 템플릿 업데이트 시에는 관련 시나리오 Spec에 별도 수정이 필요 없다.

## 템플릿 목록
| 시나리오 | 템플릿 | 주요 목적 |
|----------|--------|-----------|
| capture  | `템플릿-즉흥메모.md` | 즉흥 아이디어/TODO 기록 및 후속 작업 지정 |
| process  | `템플릿-Literature.md` | 원문 기반 자료정리 및 검색 메타데이터 축적 |
| create   | `템플릿-Permanent.md` | 핵심개념 정리 및 연결 관계 관리 |
| connect  | `템플릿-MOC.md` | 주제별 맵 작성 및 링크 허브 |
| project  | `템플릿-Project.md` | 프로젝트 계획/추적 |

## 템플릿 유지보수 원칙
- **메타데이터 추가 시**: 템플릿 프론트매터에 필드를 추가하고 `core/metadata.spec.md`의 테이블에 설명을 업데이트한다.
- **섹션 구조 변경 시**: 템플릿 본문 주석을 수정하고, 필요하다면 관련 Validator Spec에 검증 규칙을 추가한다.
- **유형별 예시**: 템플릿 주석에 간단한 예시 또는 체크리스트를 두어 에이전트가 별도 설명 없이 이해할 수 있도록 한다.

## 템플릿 로드 예시 (Pseudo)
```python
result = Desktop_Commander.run_command(
    "cd ~/Documents/docs-system/90-설정 && python3 orchestrator.py workflow process 'Large Language Models'"
)
workflow = json.loads(result)
# workflow["template"]["path"] -> 템플릿 절대 경로
# 이후 Filesystem:read_file(workflow["template"]["path"]) 로 템플릿 내용 확보
```
