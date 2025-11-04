#!/bin/bash

# Spec 동적 로더
# 사용자 입력에 따라 필요한 spec만 로드

set -e

DOCS_ROOT="/Users/seolmin.kwon/Documents/docs-system"
SPECS_DIR="$DOCS_ROOT/90-설정/specs"

# 환경변수 설정
export DOCS_PHASE=""
export DOCS_SCENARIO=""
export LOADED_SPECS=""
declare -a LOADED_SPEC_PATHS=()
SPEC_CONTENT_BUFFER=""

# 색상 정의
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

# 로그 함수
log_loading() {
    echo -e "${BLUE}⚡ Loading: $1${NC}"
}

log_loaded() {
    echo -e "${GREEN}✓ Loaded: $1${NC}"
}

# 키워드 매칭으로 시나리오 식별
identify_scenario() {
    local input="$1"
    local scenario=""
    
    # 키워드 패턴 매칭
    if [[ "$input" =~ (저장|메모|기록|아이디어|질문|할일|TODO) ]]; then
        scenario="capture"
    elif [[ "$input" =~ (정리|요약|분석|자료정리) ]]; then
        scenario="process"
    elif [[ "$input" =~ (노트.*만들|개념.*정리|핵심개념|permanent) ]]; then
        scenario="create"
    elif [[ "$input" =~ (MOC|맵.*생성|주제.*연결|개념.*구조) ]]; then
        scenario="connect"
    elif [[ "$input" =~ (프로젝트|실행.*계획) ]]; then
        scenario="project"
    elif [[ "$input" =~ (리뷰|검증|점검) ]]; then
        scenario="review"
    elif [[ "$input" =~ (찾아|보여|검색|어디) ]]; then
        scenario="search"
    else
        scenario="general"
    fi
    
    echo "$scenario"
}

# Spec 파일 읽기 (MCP 시뮬레이션)
load_spec_file() {
    local spec_file="$1"
    
    if [[ -f "$spec_file" ]]; then
        log_loading "$(basename "$spec_file")"
        
        # 실제 환경에서는 Filesystem:read_file() 호출
        # 여기서는 파일 존재 확인만
        if [[ -r "$spec_file" ]]; then
            local spec_name="$(basename "$spec_file")"
            LOADED_SPECS="$LOADED_SPECS:$spec_name"
            LOADED_SPEC_PATHS+=("$spec_file")

            # spec 내용을 버퍼에 저장 (LLM 컨텍스트 전달용)
            local content
            content="$(<"$spec_file")"
            SPEC_CONTENT_BUFFER+=$'\n'"## ===== $spec_name ====="$'\n\n'"$content"$'\n'

            export SPEC_CONTENT_BUFFER

            log_loaded "$spec_name"

            return 0
        fi
    fi
    
    return 1
}

# 시나리오별 spec 로드
load_specs_for_scenario() {
    local scenario="$1"
    local specs_to_load=()

    LOADED_SPECS=""
    LOADED_SPEC_PATHS=()
    SPEC_CONTENT_BUFFER=""

    # 항상 로드하는 기본 spec
    specs_to_load+=("$SPECS_DIR/core/structure.spec.md")
    specs_to_load+=("$SPECS_DIR/core/metadata.spec.md")
    
    # 시나리오별 spec 선택
    case "$scenario" in
        capture)
            specs_to_load+=("$SPECS_DIR/scenarios/capture.spec.md")
            ;;
        process)
            specs_to_load+=("$SPECS_DIR/scenarios/process.spec.md")
            specs_to_load+=("$SPECS_DIR/core/link-rules.spec.md")
            ;;
        create)
            specs_to_load+=("$SPECS_DIR/scenarios/create.spec.md")
            specs_to_load+=("$SPECS_DIR/core/link-rules.spec.md")
            specs_to_load+=("$SPECS_DIR/validators/link-validator.spec.md")
            ;;
        connect)
            specs_to_load+=("$SPECS_DIR/scenarios/connect.spec.md")
            specs_to_load+=("$SPECS_DIR/core/link-rules.spec.md")
            ;;
        project)
            specs_to_load+=("$SPECS_DIR/scenarios/project.spec.md")
            ;;
        review)
            specs_to_load+=("$SPECS_DIR/scenarios/review.spec.md")
            specs_to_load+=("$SPECS_DIR/validators/link-validator.spec.md")
            specs_to_load+=("$SPECS_DIR/validators/priority.spec.md")
            ;;
        search)
            specs_to_load+=("$SPECS_DIR/scenarios/search.spec.md")
            ;;
        *)
            # 일반적인 경우 모든 core spec 로드
            specs_to_load+=("$SPECS_DIR/core/link-rules.spec.md")
            ;;
    esac
    
    # spec 파일들 로드
    for spec in "${specs_to_load[@]}"; do
        load_spec_file "$spec"
    done
}

# 로드된 spec 정보 출력
print_loaded_specs() {
    echo ""
    echo "📚 Loaded Specs Summary:"
    echo "========================"
    echo "Scenario: $DOCS_SCENARIO"
    echo "Phase: $DOCS_PHASE"
    echo "Loaded files: $(echo "$LOADED_SPECS" | tr ':' '\n' | grep -v '^$' | wc -l)"
    
    # 각 spec 파일 크기 계산 (컨텍스트 추정)
    local total_lines=0
    for spec_path in "${LOADED_SPEC_PATHS[@]}"; do
        if [[ -f "$spec_path" ]]; then
            local spec_name="$(basename "$spec_path")"
            local lines=$(wc -l < "$spec_path")
            total_lines=$((total_lines + lines))
            echo "  - $spec_name: ${lines} lines"
        fi
    done
    
    echo "------------------------"
    echo "Total context: ${total_lines} lines"
    echo "Buffer size: ${#SPEC_CONTENT_BUFFER} chars"
    
    # 토큰 추정 (대략 4 chars = 1 token)
    local estimated_tokens=$((${#SPEC_CONTENT_BUFFER} / 4))
    echo "Estimated tokens: ~${estimated_tokens}"
    
    # 기존 대비 절약률 계산
    local original_lines=1392  # system_prompt.md + link_prompt.md
    local saved_percent=$(( (original_lines - total_lines) * 100 / original_lines ))
    echo "Context saved: ${saved_percent}% (vs ${original_lines} lines)"
}

# 메인 실행 함수
main() {
    local user_input="${1:-}"
    
    if [[ -z "$user_input" ]]; then
        echo "Usage: $0 \"사용자 입력\""
        echo "Example: $0 \"AI 에이전트 관련 핵심개념 만들어줘\""
        exit 1
    fi
    
    echo "🔍 Analyzing input: \"$user_input\""
    echo ""
    
    # 시나리오 식별
    DOCS_SCENARIO=$(identify_scenario "$user_input")
    export DOCS_SCENARIO
    
    echo "📎 Identified scenario: $DOCS_SCENARIO"
    echo ""
    
    # spec 로드
    load_specs_for_scenario "$DOCS_SCENARIO"
    
    # 결과 출력
    print_loaded_specs
    
    # 환경변수 export (다른 스크립트에서 사용 가능)
    export LOADED_SPECS
    export DOCS_PHASE="loaded"
    
    echo ""
    echo "✅ Ready to process with optimized context!"
}

# 스크립트 직접 실행 시
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
