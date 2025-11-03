#!/bin/bash

# 문서 시스템 검증 스크립트
# 각 시나리오별 검증 로직 구현

set -e

DOCS_ROOT="/Users/seolmin.kwon/Documents/docs-system"
SPECS_DIR="$DOCS_ROOT/90-설정/specs"

# 색상 정의
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

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
    echo -e "ℹ️  $1"
}

# 폴더 구조 검증
validate_folder_structure() {
    info "폴더 구조 검증 중..."
    
    local required_dirs=(
        "10-수집/원문"
        "10-수집/즉흥메모"
        "20-정리/자료정리"
        "20-정리/핵심개념"
        "30-연결"
        "40-실행"
        "80-보관"
        "90-설정"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$DOCS_ROOT/$dir" ]]; then
            error "필수 폴더 누락: $dir"
        fi
    done
    
    success "폴더 구조 정상"
}

# source 필드 검증
check_source_field() {
    local file="$1"
    local expected_type="$2"
    
    if [[ ! -f "$file" ]]; then
        return 1
    fi
    
    # YAML frontmatter에서 source 추출
    local source=$(grep -m1 "^source:" "$file" 2>/dev/null || echo "")
    
    if [[ -z "$source" ]]; then
        error "$file: source 필드 필수"
        return 1
    fi
    
    # source 파일 존재 확인
    local source_file=$(echo "$source" | sed 's/source: \[\[\(.*\)\]\]/\1/')
    # TODO: 실제 파일 존재 확인 로직 추가
    
    return 0
}

# MOC 연결 검증
check_moc_connection() {
    local file="$1"
    
    local moc_count=$(grep -c "\[\[맵-" "$file" 2>/dev/null || echo "0")
    
    if [[ "$moc_count" -eq 0 ]]; then
        error "$file: MOC 연결 필수 (최소 1개)"
        return 1
    fi
    
    return 0
}

# 개념 연결 검증 (권장)
check_concept_links() {
    local file="$1"
    local mode="${2:-error}"  # error 또는 warn
    
    # 다른 개념 링크 카운트 (맵- 제외)
    local concept_links=$(grep -o '\[\[개념-[^]]*\]\]' "$file" 2>/dev/null | wc -l)
    
    if [[ "$concept_links" -lt 2 ]]; then
        if [[ "$mode" == "warn" ]]; then
            warn "$file: 개념 연결 2개 이상 권장 (현재: $concept_links개)"
        else
            error "$file: 개념 연결 2개 이상 필요"
        fi
        return 1
    fi
    
    return 0
}

# 프로젝트 폴더 구조 검증
check_project_structure() {
    local project_dir="$1"
    
    if [[ ! -d "$project_dir" ]]; then
        error "프로젝트 폴더 없음: $project_dir"
        return 1
    fi
    
    local required_files=(
        "_index.md"
        "planning.md"
        "resources.md"
        "tasks.md"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$project_dir/$file" ]]; then
            warn "프로젝트 파일 누락: $project_dir/$file"
        fi
    done
    
    return 0
}

# MOC 최소 개념 검증
check_min_concepts() {
    local file="$1"
    local min_count="${2:-3}"
    
    local concept_count=$(grep -c '\[\[개념-' "$file" 2>/dev/null || echo "0")
    
    if [[ "$concept_count" -lt "$min_count" ]]; then
        error "$file: 최소 $min_count개 핵심개념 필요 (현재: $concept_count개)"
        return 1
    fi
    
    return 0
}

# 노트 타입별 검증
validate_note() {
    local note_type="$1"
    local file_path="$2"
    
    case "$note_type" in
        "자료정리")
            check_source_field "$file_path" "원문"
            ;;
        "핵심개념")
            check_source_field "$file_path" "자료정리"
            check_moc_connection "$file_path"
            check_concept_links "$file_path" "warn"
            ;;
        "MOC")
            check_min_concepts "$file_path" 3
            ;;
        "프로젝트")
            check_project_structure "$file_path"
            ;;
        *)
            warn "알 수 없는 노트 타입: $note_type"
            ;;
    esac
}

# 주간 리뷰 검증
weekly_review() {
    info "주간 리뷰 실행 중..."
    
    # 고립 노트 검색
    local isolated_notes=()
    # TODO: 백링크 0개인 노트 찾기 로직
    
    # 오래된 즉흥메모 검색 (30일 이상)
    local old_fleeting=$(find "$DOCS_ROOT/10-수집/즉흥메모" -name "*.md" -mtime +30 2>/dev/null | wc -l)
    if [[ "$old_fleeting" -gt 0 ]]; then
        warn "30일 이상 된 즉흥메모: $old_fleeting개"
    fi
    
    # 출처 없는 핵심개념 검색
    for file in "$DOCS_ROOT/20-정리/핵심개념"/*.md; do
        if [[ -f "$file" ]]; then
            check_source_field "$file" "any" 2>/dev/null || warn "출처 없음: $(basename "$file")"
        fi
    done
    
    success "주간 리뷰 완료"
}

# 전체 검증
validate_all() {
    info "전체 시스템 검증 시작..."
    
    validate_folder_structure
    
    # 각 폴더별 검증
    info "자료정리 검증 중..."
    for file in "$DOCS_ROOT/20-정리/자료정리"/*.md; do
        if [[ -f "$file" ]]; then
            validate_note "자료정리" "$file" || true
        fi
    done
    
    info "핵심개념 검증 중..."
    for file in "$DOCS_ROOT/20-정리/핵심개념"/*.md; do
        if [[ -f "$file" ]]; then
            validate_note "핵심개념" "$file" || true
        fi
    done
    
    info "MOC 검증 중..."
    for file in "$DOCS_ROOT/30-연결"/*.md; do
        if [[ -f "$file" ]]; then
            validate_note "MOC" "$file" || true
        fi
    done
    
    info "프로젝트 검증 중..."
    for project_dir in "$DOCS_ROOT/40-실행"/*; do
        if [[ -d "$project_dir" ]]; then
            validate_note "프로젝트" "$project_dir" || true
        fi
    done
    
    success "전체 검증 완료"
}

# 메인 실행 로직
main() {
    case "${1:-all}" in
        structure)
            validate_folder_structure
            ;;
        weekly)
            weekly_review
            ;;
        all)
            validate_all
            ;;
        *)
            echo "Usage: $0 {structure|weekly|all}"
            exit 1
            ;;
    esac
}

main "$@"