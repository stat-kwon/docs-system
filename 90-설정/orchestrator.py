#!/usr/bin/env python3
"""
Zettelkasten 도우미 - 시나리오 매칭, 파일명 생성, 검증

이 스크립트는 다음만 담당:
1. 시나리오 매칭 (키워드 → 시나리오)
2. 파일명 생성 규칙 반환
3. 필요한 spec 파일 목록 반환
4. 검증 수행

실제 파일 생성은 Claude + Filesystem MCP가 담당!

Usage:
    python3 orchestrator.py match <user_input>
    python3 orchestrator.py filename <scenario> <title>
    python3 orchestrator.py specs <scenario>
    python3 orchestrator.py validate <filepath>
"""

import yaml
import json
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

class ZettelkastenHelper:
    """경량 도우미 클래스"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.docs_root = Path(self.config['docs_root'])
    
    def match_scenario(self, user_input: str) -> Dict[str, Any]:
        """
        시나리오 매칭
        
        입력: 사용자 입력 문자열
        출력: {
            "scenario": "capture",
            "config": {...},
            "spec_files": [...],
            "path": "10-수집/즉흥메모"
        }
        """
        user_input_lower = user_input.lower()
        
        for scenario_name, scenario_config in self.config['scenarios'].items():
            keywords = scenario_config.get('keywords', [])
            if any(keyword in user_input_lower for keyword in keywords):
                return {
                    'scenario': scenario_name,
                    'config': scenario_config,
                    'spec_files': scenario_config.get('spec_files', []),
                    'path': scenario_config.get('path', ''),
                    'auto_execute': scenario_config.get('auto_execute', False),
                    'validation': scenario_config.get('validation', [])
                }
        
        return {
            'scenario': None,
            'error': 'No matching scenario found'
        }
    
    def get_filename(self, scenario: str, title: str, **kwargs) -> Dict[str, Any]:
        """
        파일명 생성
        
        입력: scenario, title, (optional) date, project_name
        출력: {
            "filename": "20241104-1530-제목.md",
            "template": "{date:%Y%m%d-%H%M}-{title}.md",
            "path": "10-수집/즉흥메모",
            "full_path": "/Users/.../10-수집/즉흥메모/20241104-1530-제목.md"
        }
        """
        if scenario not in self.config['scenarios']:
            return {'error': f'Unknown scenario: {scenario}'}
        
        rule = self.config['scenarios'][scenario]
        template = rule.get('filename_template')
        
        if not template:
            return {'error': f'No filename template for scenario: {scenario}'}
        
        # 파라미터 준비
        params = {'title': title}
        params['date'] = kwargs.get('date', datetime.now())
        
        # project_name 처리
        if 'project_name' in kwargs:
            params['project_name'] = kwargs['project_name']
        
        # suffix 처리 (create 시나리오)
        if rule.get('needs_suffix'):
            params['suffix'] = self._find_next_suffix(scenario, params['date'], title)
        
        # 파일명 생성
        filename = template.format(**params)
        
        # 경로 생성
        path_template = rule['path']
        if '{project_name}' in path_template:
            path = path_template.format(project_name=params.get('project_name', 'untitled'))
        else:
            path = path_template
        
        full_path = self.docs_root / path / filename
        
        return {
            'filename': filename,
            'template': template,
            'path': path,
            'full_path': str(full_path),
            'needs_suffix': rule.get('needs_suffix', False)
        }
    
    def _find_next_suffix(self, scenario: str, date: datetime, title: str) -> str:
        """suffix 자동 증가 (a, b, c, ...)"""
        rule = self.config['scenarios'][scenario]
        path = self.docs_root / rule['path']
        
        if not path.exists():
            return 'a'
        
        date_str = date.strftime("%Y%m%d")
        suffix_chars = self.config.get('suffix', {}).get('chars', 'abcdefghij')
        
        for suffix in suffix_chars:
            test_name = f"개념-{date_str}{suffix}-{title}.md"
            if not (path / test_name).exists():
                return suffix
        
        # 모든 suffix 사용됨
        return 'z'
    
    def get_specs(self, scenario: str) -> Dict[str, Any]:
        """
        필요한 spec 파일 목록 반환
        
        출력: {
            "spec_files": [
                "scenarios/capture.spec.md",
                "core/metadata.spec.md"
            ],
            "full_paths": [
                "/Users/.../90-설정/specs/scenarios/capture.spec.md",
                ...
            ]
        }
        """
        if scenario not in self.config['scenarios']:
            return {'error': f'Unknown scenario: {scenario}'}
        
        spec_files = self.config['scenarios'][scenario].get('spec_files', [])
        full_paths = [str(self.docs_root / '90-설정' / 'specs' / f) for f in spec_files]
        
        return {
            'spec_files': spec_files,
            'full_paths': full_paths
        }
    
    def validate(self, filepath: str) -> Dict[str, Any]:
        """
        파일 검증
        
        입력: 파일 경로
        출력: {
            "status": "success" | "error",
            "errors": [...],
            "warnings": [...]
        }
        """
        path = Path(filepath)
        
        if not path.exists():
            return {
                'status': 'error',
                'errors': [f'File not found: {filepath}']
            }
        
        try:
            content = path.read_text(encoding='utf-8')
        except Exception as e:
            return {
                'status': 'error',
                'errors': [f'Cannot read file: {e}']
            }
        
        errors = []
        warnings = []
        
        # Frontmatter 파싱
        match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if not match:
            errors.append('No frontmatter found')
            return {
                'status': 'error',
                'errors': errors
            }
        
        try:
            frontmatter = yaml.safe_load(match.group(1))
        except Exception as e:
            errors.append(f'Invalid YAML frontmatter: {e}')
            return {
                'status': 'error',
                'errors': errors
            }
        
        # 전역 검증 규칙
        validation_config = self.config.get('validation', {})
        
        # source_chain 검증
        if validation_config.get('source_chain') == 'required':
            if 'source' not in frontmatter or not frontmatter['source']:
                errors.append('Missing required field: source')
        
        # MOC 링크 검증
        moc_link_min = validation_config.get('moc_link_min', 0)
        if moc_link_min > 0:
            moc_links = re.findall(r'\[\[맵-[^\]]+\]\]', content)
            if len(moc_links) < moc_link_min:
                warnings.append(
                    f'권장: MOC 링크 {moc_link_min}개 이상 추가 (현재 {len(moc_links)}개)'
                )
        
        # 개념 링크 검증
        concept_link_min = validation_config.get('concept_link_min', 0)
        if concept_link_min > 0:
            concept_links = re.findall(r'\[\[개념-[^\]]+\]\]', content)
            if len(concept_links) < concept_link_min:
                warnings.append(
                    f'권장: 개념 링크 {concept_link_min}개 이상 추가 (현재 {len(concept_links)}개)'
                )
        
        # 태그 검증
        if 'tags' not in frontmatter or not frontmatter['tags']:
            warnings.append('권장: tags 필드 추가')
        
        if errors:
            return {
                'status': 'error',
                'errors': errors,
                'warnings': warnings
            }
        else:
            return {
                'status': 'success',
                'warnings': warnings
            }
    
    def list_mocs(self) -> Dict[str, Any]:
        """
        /30-연결/ 폴더의 MOC 목록 반환
        
        출력: {
            "mocs": [
                {
                    "filename": "맵-AI시스템.md",
                    "title": "AI시스템",
                    "path": "/30-연결/맵-AI시스템.md",
                    "tags": ["#ai", "#system"],
                    "linked_concepts": 5
                }
            ]
        }
        """
        moc_dir = self.docs_root / '30-연결'
        
        if not moc_dir.exists():
            return {
                'mocs': [],
                'warning': 'MOC directory not found'
            }
        
        mocs = []
        for file_path in moc_dir.glob('맵-*.md'):
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Frontmatter 파싱
                match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
                if match:
                    frontmatter = yaml.safe_load(match.group(1))
                    tags = frontmatter.get('tags', [])
                else:
                    tags = []
                
                # 제목 추출 (파일명에서)
                title = file_path.stem.replace('맵-', '')
                
                # 연결된 개념 수 카운트
                concept_links = re.findall(r'\[\[개념-[^\]]+\]\]', content)
                
                mocs.append({
                    'filename': file_path.name,
                    'title': title,
                    'path': str(file_path.relative_to(self.docs_root)),
                    'full_path': str(file_path),
                    'tags': tags,
                    'linked_concepts': len(concept_links)
                })
            except Exception as e:
                # 파일 읽기 실패 시 건너뛰기
                continue
        
        return {
            'mocs': mocs,
            'count': len(mocs)
        }
    
    def list_concepts(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        /20-정리/핵심개념/ 폴더의 개념 목록 반환
        
        입력: filters = {"tags": ["#ai"], "after_date": "20241101"}
        출력: {
            "concepts": [
                {
                    "filename": "개념-20241103a-딥러닝.md",
                    "title": "딥러닝",
                    "path": "/20-정리/핵심개념/개념-20241103a-딥러닝.md",
                    "tags": ["#ai", "#neural-network"],
                    "created": "2024-11-03"
                }
            ]
        }
        """
        concept_dir = self.docs_root / '20-정리' / '핵심개념'
        
        if not concept_dir.exists():
            return {
                'concepts': [],
                'warning': 'Concepts directory not found'
            }
        
        filters = filters or {}
        tag_filters = filters.get('tags', [])
        after_date = filters.get('after_date')
        
        concepts = []
        for file_path in concept_dir.glob('개념-*.md'):
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Frontmatter 파싱
                match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
                if match:
                    frontmatter = yaml.safe_load(match.group(1))
                    tags = frontmatter.get('tags', [])
                    created = frontmatter.get('created', '')
                    # date 객체를 문자열로 변환
                    if hasattr(created, 'strftime'):
                        created = created.strftime('%Y-%m-%d')
                    elif not isinstance(created, str):
                        created = str(created)
                else:
                    tags = []
                    created = ''
                
                # 필터링: 날짜
                if after_date and created < after_date:
                    continue
                
                # 필터링: 태그
                if tag_filters:
                    if not any(tag in tags for tag in tag_filters):
                        continue
                
                # 제목 추출 (파일명에서)
                # 개념-20241103a-딥러닝.md → 딥러닝
                name_match = re.match(r'개념-\d{8}[a-z]-(.+)\.md', file_path.name)
                title = name_match.group(1) if name_match else file_path.stem
                
                concepts.append({
                    'filename': file_path.name,
                    'title': title,
                    'path': str(file_path.relative_to(self.docs_root)),
                    'full_path': str(file_path),
                    'tags': tags,
                    'created': created
                })
            except Exception as e:
                # 파일 읽기 실패 시 건너뛰기
                continue
        
        return {
            'concepts': concepts,
            'count': len(concepts)
        }
    
    def get_file_preview(self, filepath: str, lines: int = 5) -> Dict[str, Any]:
        """
        파일 미리보기 (frontmatter + 첫 N줄)
        
        출력: {
            "frontmatter": {...},
            "preview": "첫 5줄 내용...",
            "tags": [...],
            "links": [...]
        }
        """
        path = Path(filepath)
        
        if not path.exists():
            return {
                'error': f'File not found: {filepath}'
            }
        
        try:
            content = path.read_text(encoding='utf-8')
        except Exception as e:
            return {
                'error': f'Cannot read file: {e}'
            }
        
        # Frontmatter 파싱
        match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
                # date 객체를 문자열로 변환
                for key, value in frontmatter.items():
                    if hasattr(value, 'strftime'):
                        frontmatter[key] = value.strftime('%Y-%m-%d')
                body = match.group(2)
            except Exception as e:
                return {
                    'error': f'Invalid YAML frontmatter: {e}'
                }
        else:
            frontmatter = {}
            body = content
        
        # 첫 N줄 추출
        body_lines = body.strip().split('\n')
        preview_lines = body_lines[:lines]
        preview = '\n'.join(preview_lines)
        
        # 링크 추출
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        
        return {
            'filename': path.name,
            'frontmatter': frontmatter,
            'preview': preview,
            'tags': frontmatter.get('tags', []),
            'links': links,
            'total_lines': len(body_lines)
        }

def main():
    """CLI 인터페이스"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'Usage: orchestrator.py <command> [args]',
            'commands': ['match', 'filename', 'specs', 'validate', 'list_mocs', 'list_concepts', 'preview']
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    config_path = Path(__file__).parent / 'rules.yaml'
    
    if not config_path.exists():
        print(json.dumps({
            'error': f'Config file not found: {config_path}'
        }))
        sys.exit(1)
    
    helper = ZettelkastenHelper(str(config_path))
    
    if command == 'match':
        # python3 orchestrator.py match "AI 메모 저장"
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: orchestrator.py match <user_input>'}))
            sys.exit(1)
        
        user_input = sys.argv[2]
        result = helper.match_scenario(user_input)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'filename':
        # python3 orchestrator.py filename capture "AI개념"
        if len(sys.argv) < 4:
            print(json.dumps({'error': 'Usage: orchestrator.py filename <scenario> <title>'}))
            sys.exit(1)
        
        scenario = sys.argv[2]
        title = sys.argv[3]
        result = helper.get_filename(scenario, title)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'specs':
        # python3 orchestrator.py specs capture
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: orchestrator.py specs <scenario>'}))
            sys.exit(1)
        
        scenario = sys.argv[2]
        result = helper.get_specs(scenario)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'validate':
        # python3 orchestrator.py validate /path/to/file.md
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: orchestrator.py validate <filepath>'}))
            sys.exit(1)
        
        filepath = sys.argv[2]
        result = helper.validate(filepath)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'list_mocs':
        # python3 orchestrator.py list_mocs
        result = helper.list_mocs()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'list_concepts':
        # python3 orchestrator.py list_concepts
        # python3 orchestrator.py list_concepts '{"tags": ["#ai"]}'
        filters = None
        if len(sys.argv) > 2:
            try:
                filters = json.loads(sys.argv[2])
            except:
                pass
        result = helper.list_concepts(filters)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'preview':
        # python3 orchestrator.py preview /path/to/file.md
        # python3 orchestrator.py preview /path/to/file.md 10
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: orchestrator.py preview <filepath> [lines]'}))
            sys.exit(1)
        
        filepath = sys.argv[2]
        lines = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        result = helper.get_file_preview(filepath, lines)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        print(json.dumps({
            'error': f'Unknown command: {command}',
            'available': ['match', 'filename', 'specs', 'validate', 'list_mocs', 'list_concepts', 'preview']
        }))
        sys.exit(1)

if __name__ == '__main__':
    main()