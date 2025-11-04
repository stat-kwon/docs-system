#!/bin/bash

# Spec 동적 로더 v2 - Orchestrator와 통합
# 사용자 입력에 따라 필요한 spec만 로드

set -e

# 환경변수 기반 경로 설정
DOCS_ROOT="${DOCS_HOME:-$(dirname "$(dirname "$(readlink -f "$0")")")}"
SPECS_DIR="$DOCS_ROOT/90-설정/specs"
ORCHESTRATOR="$DOCS_ROOT/90-설정/orchestrator.py"

# 환경변수 설정
export DOCS_PHASE=""
export DOCS_SCENARIO=""
export LOADED_SPECS=""
declare -a LOADED_SPEC_PATHS=()
SPEC_CONTENT_BUFFER=""

# 색상 정의
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# 로그 함수
log_loading() {
    echo -e "${BLUE}⚡ Loading: $1${NC}" >&2
}

log_loaded() {
    echo -e "${GREEN}✓ Loaded: $1${NC}" >&2
}

log_error() {
    echo -e "${RED}✗ Error: $1${NC}" >&2
}

log_warning() {
    echo -e "${YELLOW}⚠ Warning: $1${NC}" >&2
}

# Orchestrator를 통한 시나리오 식별
identify_scenario_via_orchestrator() {
    local input="$1"
    
    if [[ ! -f "$ORCHESTRATOR" ]]; then
        log_error "Orchestrator not found: $ORCHESTRATOR"
        return 1
    fi
    
    # orchestrator.py match 명령 실행
    local result
    result=$(python3 "$ORCHESTRATOR" match "$input" 2>/dev/null)
    
    if [[ $? -ne 0 ]]; then
        log_error "Failed to identify scenario via orchestrator"
        echo "general"
        return 1
    fi
    
    # JSON 결과에서 scenario 추출 (jq가 없을 경우 대비)
    if command -v jq &> /dev/null; then
        scenario=$(echo "$result" | jq -r '.scenario // "general"')
    else
        # 간단한 grep 기반 파싱
        scenario=$(echo "$result" | grep -o '"scenario": "[^"]*"' | cut -d'"' -f4)
        if [[ -z "$scenario" || "$scenario" == "null" ]]; then
            scenario="general"
        fi
    fi
    
    echo "$scenario"
}

# Spec 파일 읽기
load_spec_file() {
    local spec_file="$1"
    local is_optional="${2:-false}"
    
    if [[ ! -f "$spec_file" ]]; then
        if [[ "$is_optional" == "false" ]]; then
            log_error "Required spec not found: $(basename "$spec_file")"
            return 1
        else
            log_warning "Optional spec not found: $(basename "$spec_file")"
            return 0
        fi
    fi
    
    if [[ ! -r "$spec_file" ]]; then
        log_error "Cannot read spec: $(basename "$spec_file")"
        return 1
    fi
    
    log_loading "$(basename "$spec_file")"
    
    local spec_name="$(basename "$spec_file")"
    LOADED_SPECS="$LOADED_SPECS:$spec_name"
    LOADED_SPEC_PATHS+=("$spec_file")
    
    # spec 내용을 버퍼에 저장
    local content
    if ! content="$(<"$spec_file")"; then
        log_error "Failed to read content from $spec_name"
        return 1
    fi
    
    SPEC_CONTENT_BUFFER+=$'\n'"## ===== $spec_name ====="$'\n\n'"$content"$'\n'
    export SPEC_CONTENT_BUFFER
    
    log_loaded "$spec_name"
    return 0
}

# Orchestrator에서 spec 목록 가져오기
get_specs_from_orchestrator() {
    local scenario="$1"
    
    if [[ ! -f "$ORCHESTRATOR" ]]; then
        log_error "Orchestrator not found"
        return 1
    fi
    
    # orchestrator.py specs 명령 실행
    local result
    result=$(python3 "$ORCHESTRATOR" specs "$scenario" 2>/dev/null)
    
    if [[ $? -ne 0 ]]; then
        log_error "Failed to get specs from orchestrator"
        return 1
    fi
    
    # spec_files 배열 추출
    if command -v jq &> /dev/null; then
        echo "$result" | jq -r '.spec_files[]?' 2>/dev/null
    else
        # 간단한 grep 기반 파싱
        echo "$result" | grep -o '"spec_files": \[[^]]*\]' | sed 's/.*\[//;s/\].*//;s/"//g;s/,/\n/g'
    fi
}

# 시나리오별 spec 로드
load_specs_for_scenario() {
    local scenario="$1"
    local specs_to_load=()
    
    LOADED_SPECS=""
    LOADED_SPEC_PATHS=()
    SPEC_CONTENT_BUFFER=""
    
    # Orchestrator에서 spec 목록 가져오기
    local spec_files
    spec_files=$(get_specs_from_orchestrator "$scenario")
    
    if [[ -z "$spec_files" ]]; then
        log_warning "No specs defined for scenario: $scenario. Loading defaults."
        # 기본 spec만 로드
        specs_to_load+=("$SPECS_DIR/core/structure.spec.md")
        specs_to_load+=("$SPECS_DIR/core/metadata.spec.md")
    else
        # Orchestrator가 제안한 spec 로드
        while IFS= read -r spec_file; do
            if [[ -n "$spec_file" ]]; then
                specs_to_load+=("$SPECS_DIR/$spec_file")
            fi
        done <<< "$spec_files"
    fi
    
    # spec 파일들 로드
    local load_failed=false
    for spec in "${specs_to_load[@]}"; do
        # core/ 디렉토리의 spec은 필수, 나머지는 선택적
        local is_optional="false"
        if [[ "$spec" != *"/core/"* ]]; then
            is_optional="true"
        fi
        
        if ! load_spec_file "$spec" "$is_optional"; then
            if [[ "$is_optional" == "false" ]]; then
                load_failed=true
                break
            fi
        fi
    done
    
    if [[ "$load_failed" == "true" ]]; then
        log_error "Failed to load required specs"
        return 1
    fi
    
    return 0
}

# 로드된 spec 정보 출력
print_loaded_specs() {
    echo "" >&2
    echo "📚 Loaded Specs Summary:" >&2
    echo "========================" >&2
    echo "Scenario: $DOCS_SCENARIO" >&2
    echo "Phase: $DOCS_PHASE" >&2
    
    local loaded_count=$(echo "$LOADED_SPECS" | tr ':' '\n' | grep -v '^$' | wc -l)
    echo "Loaded files: $loaded_count" >&2
    
    # 각 spec 파일 크기 계산
    local total_lines=0
    for spec_path in "${LOADED_SPEC_PATHS[@]}"; do
        if [[ -f "$spec_path" ]]; then
            local spec_name="$(basename "$spec_path")"
            local lines=$(wc -l < "$spec_path")
            total_lines=$((total_lines + lines))
            echo "  - $spec_name: ${lines} lines" >&2
        fi
    done
    
    echo "------------------------" >&2
    echo "Total context: ${total_lines} lines" >&2
    echo "Buffer size: ${#SPEC_CONTENT_BUFFER} chars" >&2
    
    # 토큰 추정
    local estimated_tokens=$((${#SPEC_CONTENT_BUFFER} / 4))
    echo "Estimated tokens: ~${estimated_tokens}" >&2
    
    # 기존 대비 절약률 계산
    local original_lines=1392
    if [[ $total_lines -gt 0 ]]; then
        local saved_percent=$(( (original_lines - total_lines) * 100 / original_lines ))
        echo "Context saved: ${saved_percent}% (vs ${original_lines} lines)" >&2
    fi
}

# 메인 실행 함수
main() {
    local user_input="${1:-}"
    
    if [[ -z "$user_input" ]]; then
        echo "Usage: $0 \"사용자 입력\"" >&2
        echo "Example: $0 \"AI 에이전트 관련 핵심개념 만들어줘\"" >&2
        exit 1
    fi
    
    echo "🔍 Analyzing input: \"$user_input\"" >&2
    echo "" >&2
    
    # Orchestrator를 통한 시나리오 식별
    DOCS_SCENARIO=$(identify_scenario_via_orchestrator "$user_input")
    export DOCS_SCENARIO
    
    echo "📎 Identified scenario: $DOCS_SCENARIO" >&2
    echo "" >&2
    
    # spec 로드
    if ! load_specs_for_scenario "$DOCS_SCENARIO"; then
        log_error "Failed to load specs for scenario: $DOCS_SCENARIO"
        exit 1
    fi
    
    # 결과 출력
    print_loaded_specs
    
    # 환경변수 export
    export LOADED_SPECS
    export DOCS_PHASE="loaded"
    
    echo "" >&2
    echo "✅ Ready to process with optimized context!" >&2
    
    # 실제 spec 내용을 stdout으로 출력 (Claude가 읽을 수 있도록)
    echo "$SPEC_CONTENT_BUFFER"
}

# 스크립트 직접 실행 시
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi