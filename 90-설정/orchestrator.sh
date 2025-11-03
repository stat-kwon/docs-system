#!/bin/bash

# 문서 시스템 Orchestrator
# 전체 워크플로우 관리 및 실행

set -e

DOCS_ROOT="/Users/seolmin.kwon/Documents/docs-system"
SPECS_DIR="$DOCS_ROOT/90-설정/specs"
SCRIPTS_DIR="$DOCS_ROOT/90-설정"

# 색상 정의
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 로그 함수
error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

action() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

# 초기화
init() {
    action "문서 시스템 초기화 중..."
    
    # 필요한 스크립트 실행 권한 설정
    chmod +x "$SCRIPTS_DIR"/*.sh 2>/dev/null || true
    
    # 폴더 구조 검증
    "$SCRIPTS_DIR/validate.sh" structure
    
    # 환경변수 초기화
    export DOCS_SYSTEM_VERSION="1.0"
    export DOCS_ROOT="$DOCS_ROOT"
    export DOCS_PHASE="initialized"
    
    success "초기화 완료"
}

# 캡처 작업 (즉흥메모)
capture() {
    local type="${1:-idea}"
    local content="${2:-}"
    
    action "캡처 작업 실행: $type"
    
    # spec 로드
    source "$SCRIPTS_DIR/loader.sh"
    load_specs_for_scenario "capture"
    
    # 파일명 생성
    local timestamp=$(date +"%Y%m%d-%H%M")
    local filename="$DOCS_ROOT/10-수집/즉흥메모/${timestamp}-${type}.md"
    
    # 템플릿 확인
    local template="$DOCS_ROOT/90-설정/템플릿-즉흥메모.md"
    if [[ ! -f "$template" ]]; then
        warn "템플릿 없음, 기본 구조 사용"
        cat > "$filename" <<EOF
---
type: $type
status: pending
created: $(date +"%Y-%m-%d")
---

# $content

EOF
    else
        # 템플릿 복사 후 수정
        cp "$template" "$filename"
        # TODO: 템플릿 변수 치환
    fi
    
    success "캡처 완료: $filename"
}

# 프로세스 작업 (자료정리)
process() {
    local source_file="${1:-}"
    
    if [[ -z "$source_file" ]]; then
        error "원문 파일을 지정해주세요"
    fi
    
    action "자료정리 생성: $source_file"
    
    # spec 로드
    source "$SCRIPTS_DIR/loader.sh"
    load_specs_for_scenario "process"
    
    # 원문 파일 확인
    if [[ ! -f "$DOCS_ROOT/10-수집/원문/$source_file" ]]; then
        error "원문 파일을 찾을 수 없습니다: $source_file"
    fi
    
    # 파일명 생성
    local date_part=$(date +"%Y%m%d")
    local topic=$(echo "$source_file" | sed 's/.*-//' | sed 's/\.md//')
    local filename="$DOCS_ROOT/20-정리/자료정리/정리-${date_part}-${topic}.md"
    
    # 기본 구조 생성
    cat > "$filename" <<EOF
---
type: literature
source: [[$source_file]]
created: $(date +"%Y-%m-%d")
tags: [literature/${topic}]
---

# 정리: $topic

## 메타정보
- **출처**: [[$source_file]]
- **작성일**: $(date +"%Y-%m-%d")
- **태그**: #literature/${topic}

## 핵심 요약
[자료정리 내용]

## 주요 개념
1. 개념1: 설명
2. 개념2: 설명

## 인사이트
- 중요한 발견
- 응용 가능성
EOF
    
    success "자료정리 생성: $filename"
    
    # 검증
    "$SCRIPTS_DIR/validate.sh" note "자료정리" "$filename" || true
}

# 핵심개념 추출
extract() {
    local concept="${1:-}"
    local source="${2:-}"
    
    action "핵심개념 추출: $concept"
    
    # spec 로드
    source "$SCRIPTS_DIR/loader.sh"
    load_specs_for_scenario "create"
    
    # 파일명 생성
    local date_part=$(date +"%Y%m%d")
    local suffix="a"  # TODO: 동일 날짜 파일 체크 후 증가
    local filename="$DOCS_ROOT/20-정리/핵심개념/개념-${date_part}${suffix}-${concept}.md"
    
    # 기본 구조 생성
    cat > "$filename" <<EOF
---
type: permanent
source: [[$source]]
created: $(date +"%Y-%m-%d")
tags: [permanent/${concept}]
---

# $concept

## 정의
[100줄 이내로 단일 개념 설명]

## 연결된 개념
- MOC: [[맵-주제]] ✅ 필수
- 관련 개념: [[개념1]], [[개념2]] 🔶 권장

## 참고
- **출처**: [[$source]]
EOF
    
    success "핵심개념 생성: $filename"
    
    # MOC 연결 제안
    warn "MOC 연결이 필요합니다. 적절한 MOC를 선택하거나 새로 생성하세요."
    
    # 검증
    "$SCRIPTS_DIR/validate.sh" note "핵심개념" "$filename" || true
}

# MOC 생성
connect() {
    local topic="${1:-}"
    
    action "MOC 생성: $topic"
    
    # spec 로드
    source "$SCRIPTS_DIR/loader.sh"
    load_specs_for_scenario "connect"
    
    local filename="$DOCS_ROOT/30-연결/맵-${topic}.md"
    
    # MOC 구조 생성
    cat > "$filename" <<EOF
---
type: moc
created: $(date +"%Y-%m-%d")
tags: [moc/${topic}]
---

# 맵-${topic}

## 핵심 개념 (최소 3개)
- [[개념1]] - 설명
- [[개념2]] - 설명
- [[개념3]] - 설명

## 관련 MOC
- [[맵-상위주제]] (상위)
- [[맵-관련주제]] (관련)

## 구조도
\`\`\`mermaid
graph TD
    A[${topic}] --> B[개념1]
    A --> C[개념2]
    A --> D[개념3]
\`\`\`

## 자동 목록
\`\`\`dataview
TABLE file.mtime as "수정일"
FROM [[]]
WHERE contains(tags, "${topic}")
SORT file.mtime DESC
\`\`\`
EOF
    
    success "MOC 생성: $filename"
    warn "최소 3개의 핵심개념을 연결해주세요"
}

# 프로젝트 생성
project() {
    local project_name="${1:-}"
    
    if [[ -z "$project_name" ]]; then
        error "프로젝트 이름을 지정해주세요"
    fi
    
    action "프로젝트 생성: $project_name"
    
    # spec 로드
    source "$SCRIPTS_DIR/loader.sh"
    load_specs_for_scenario "project"
    
    # 사용자 확인 (스크립트 실행 시)
    if [[ -t 0 ]]; then
        read -p "⚠️  프로젝트 폴더를 생성하시겠습니까? (y/n): " confirm
        if [[ "$confirm" != "y" ]]; then
            warn "프로젝트 생성 취소"
            return 1
        fi
    fi
    
    # 폴더 생성
    local project_dir="$DOCS_ROOT/40-실행/$project_name"
    if [[ -d "$project_dir" ]]; then
        error "프로젝트 폴더가 이미 존재합니다: $project_name"
    fi
    
    mkdir -p "$project_dir"
    
    local today=$(date +"%Y-%m-%d")
    local date_part=$(date +"%Y%m%d")
    
    # 1. _index.md 생성 (템플릿 기반)
    local template="$DOCS_ROOT/90-설정/템플릿-Project.md"
    if [[ -f "$template" ]]; then
        # 템플릿 변수 치환
        sed -e "s/{{title}}/$project_name/g" \
            -e "s/{{date:YYYY-MM-DD}}/$today/g" \
            -e "s/{{date:YYYYMMDD}}/$date_part/g" \
            "$template" > "$project_dir/_index.md"
    else
        # 기본 구조
        cat > "$project_dir/_index.md" <<EOF
---
type: project
status: planning
created: $today
tags: [project/$project_name]
---

# $project_name

## 📋 프로젝트 개요
[프로젝트 설명]

## 🎯 목표
1. 목표 1
2. 목표 2

## 📅 일정
- **시작일**: $today
- **종료일**: 
- **현재 상태**: planning

## 🔗 관련 노트
- [[관련 개념]]
- [[관련 자료정리]]

## ✅ 작업 목록
- [ ] 작업 1
- [ ] 작업 2
EOF
    fi
    
    # 2. planning.md 생성
    cat > "$project_dir/planning.md" <<EOF
---
type: project-doc
parent: [[$project_name/_index]]
created: $today
---

# 계획: $project_name

## Phase 1: 준비
- [ ] 요구사항 정의
- [ ] 자료 조사
- [ ] 환경 설정

## Phase 2: 실행
- [ ] 핵심 기능 구현
- [ ] 테스트
- [ ] 문서화

## Phase 3: 완료
- [ ] 최종 검토
- [ ] 배포
- [ ] 회고

## 타임라인
\`\`\`mermaid
gantt
    title $project_name
    dateFormat YYYY-MM-DD
    section Phase 1
    준비        :a1, $today, 7d
    section Phase 2
    실행        :a2, after a1, 14d
    section Phase 3
    완료        :a3, after a2, 7d
\`\`\`
EOF
    
    # 3. resources.md 생성
    cat > "$project_dir/resources.md" <<EOF
---
type: project-doc
parent: [[$project_name/_index]]
created: $today
---

# 참고 자료: $project_name

## 핵심 개념
- [[개념1]]
- [[개념2]]

## 자료정리
- [[정리1]]
- [[정리2]]

## 관련 MOC
- [[맵-주제]]

## 외부 링크
- [링크1](https://example.com)
- [링크2](https://example.com)
EOF
    
    # 4. tasks.md 생성
    cat > "$project_dir/tasks.md" <<EOF
---
type: project-doc
parent: [[$project_name/_index]]
created: $today
---

# 작업 목록: $project_name

## 🔴 긴급
- [ ] 긴급 작업 📅 $today 🔴

## 🟡 중요
- [ ] 중요 작업 🟡

## 🟢 일반
- [ ] 일반 작업 🟢

## ✅ 완료
- [x] 완료된 작업 ✅ $today
EOF
    
    success "프로젝트 생성 완료: $project_dir"
    info "📁 생성된 파일:"
    info "  - _index.md (프로젝트 개요)"
    info "  - planning.md (계획)"
    info "  - resources.md (참고 자료)"
    info "  - tasks.md (작업 목록)"
    
    # 검증
    "$SCRIPTS_DIR/validate.sh" structure "$project_dir" || true
}

# 리뷰 실행
review() {
    local type="${1:-weekly}"
    
    action "리뷰 실행: $type"
    
    # spec 로드
    source "$SCRIPTS_DIR/loader.sh"
    load_specs_for_scenario "review"
    
    # 검증 스크립트 실행
    "$SCRIPTS_DIR/validate.sh" "$type"
}

# 도움말
show_help() {
    cat <<EOF
📚 문서 시스템 Orchestrator

사용법: $0 <command> [options]

Commands:
  init                      시스템 초기화
  capture <type> [content]  즉흥메모 캡처 (idea/question/todo)
  process <source>          자료정리 생성
  extract <concept> <source> 핵심개념 추출
  connect <topic>           MOC 생성
  project <name>            프로젝트 생성
  review [type]             리뷰 실행 (weekly/monthly/all)
  validate [type]           검증 실행
  help                      도움말 표시

Examples:
  $0 capture idea "AI 에이전트 아이디어"
  $0 process "20241102-article.md"
  $0 extract "에이전트통신" "정리-20241102-AI.md"
  $0 connect "AI시스템"
  $0 project "Data-Platform-구축"
  $0 review weekly

Environment Variables:
  DOCS_ROOT       문서 시스템 루트 경로
  DOCS_SCENARIO   현재 시나리오
  DOCS_PHASE      현재 단계
EOF
}

# 메인 실행
main() {
    local command="${1:-help}"
    shift || true
    
    case "$command" in
        init)
            init
            ;;
        capture)
            capture "$@"
            ;;
        process)
            process "$@"
            ;;
        extract)
            extract "$@"
            ;;
        connect)
            connect "$@"
            ;;
        project)
            project "$@"
            ;;
        review)
            review "$@"
            ;;
        validate)
            "$SCRIPTS_DIR/validate.sh" "$@"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "알 수 없는 명령: $command"
            show_help
            exit 1
            ;;
    esac
}

# 스크립트 직접 실행 시
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi