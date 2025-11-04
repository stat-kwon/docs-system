#!/usr/bin/env python3
"""
Zettelkasten 도우미 v4 - 단순화 버전
Claude Desktop이 시나리오를 판별하고, 이 스크립트는 실행만 담당
"""

import os
import yaml
import json
import sys
import re
import logging
import unicodedata
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

class ZettelkastenHelper:
    """경량 도우미 클래스 - 시나리오 매칭 제거"""
    
    def __init__(self, config_path: str):
        # 로깅 설정
        self._setup_logging()
        
        # 설정 로드
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            self.logger.info(f"Configuration loaded from {config_path}")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to load config: {e}")
            raise
        
        # 환경 변수 우선, 없으면 config, 최종적으로 현재 디렉토리
        docs_root = os.environ.get('DOCS_HOME')
        if docs_root:
            self.docs_root = Path(docs_root)
            self.logger.info(f"Using DOCS_HOME from environment: {self.docs_root}")
        elif 'docs_root' in self.config:
            self.docs_root = Path(self.config['docs_root'])
            self.logger.info(f"Using docs_root from config: {self.docs_root}")
        else:
            # 현재 스크립트 위치 기준으로 상위 디렉토리 사용
            self.docs_root = Path(__file__).parent.parent
            self.logger.info(f"Using default docs_root: {self.docs_root}")
        
        # 경로 검증
        if not self.docs_root.exists():
            self.logger.warning(f"docs_root does not exist: {self.docs_root}")
    
    def _setup_logging(self):
        """로깅 시스템 설정"""
        log_level = os.environ.get('LOG_LEVEL', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stderr)  # stderr로 출력해 stdout과 분리
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_scenario_info(self, scenario: str) -> Dict[str, Any]:
        """
        시나리오 정보 반환 (Claude Desktop이 시나리오 판별 후 호출)
        """
        if scenario not in self.config['scenarios']:
            # 기본 시나리오 찾기
            default_scenario = 'search'
            for name, config in self.config['scenarios'].items():
                if config.get('is_default', False):
                    default_scenario = name
                    break
            scenario = default_scenario
            self.logger.warning(f"Unknown scenario '{scenario}', using default '{default_scenario}'")
        
        scenario_config = self.config['scenarios'][scenario]
        
        return {
            'scenario': scenario,
            'description': scenario_config.get('description', ''),
            'spec_files': scenario_config.get('spec_files', []),
            'path': scenario_config.get('path', ''),
            'filename_template': scenario_config.get('filename_template', ''),
            'auto_execute': scenario_config.get('auto_execute', False),
            'validation': scenario_config.get('validation', []),
            'read_only': scenario_config.get('read_only', False),
            'needs_suffix': scenario_config.get('needs_suffix', False)
        }
    
    def get_filename(self, scenario: str, title: str, **kwargs) -> Dict[str, Any]:
        """파일명 생성 - 슬러그화 및 안전한 파일명 생성"""
        if scenario not in self.config['scenarios']:
            self.logger.error(f"Unknown scenario: {scenario}")
            return {'error': f'Unknown scenario: {scenario}'}
        
        rule = self.config['scenarios'][scenario]
        template = rule.get('filename_template')
        
        if not template:
            self.logger.error(f"No filename template for scenario: {scenario}")
            return {'error': f'No filename template for scenario: {scenario}'}
        
        # 제목 슬러그화 (공백, 특수문자 처리)
        safe_title = self._slugify(title)
        self.logger.debug(f"Title slugified: '{title}' -> '{safe_title}'")
        
        # 파라미터 준비
        params = {'title': safe_title}
        
        # 날짜/시간 처리
        now = kwargs.get('date', datetime.now())
        if hasattr(now, 'strftime'):
            params['date'] = now.strftime('%Y%m%d')
            params['time'] = now.strftime('%H%M')
            params['datetime'] = now.strftime('%Y%m%d-%H%M')
        else:
            params['date'] = str(now)[:10].replace('-', '')
            params['time'] = '0000'
            params['datetime'] = params['date'] + '-0000'
        
        # 프로젝트명 처리
        if 'project_name' in kwargs:
            params['project_name'] = self._slugify(kwargs['project_name'])
        
        # suffix 처리
        if rule.get('needs_suffix'):
            params['suffix'] = self._find_next_suffix(scenario, params['date'], safe_title, template)
        
        # 파일명 생성
        try:
            filename = template.format(**params)
        except KeyError as e:
            self.logger.error(f"Missing template parameter: {e}")
            return {'error': f'Missing template parameter: {e}'}
        
        # 경로 생성
        path_template = rule['path']
        if '{project_name}' in path_template:
            path = path_template.format(project_name=params.get('project_name', 'untitled'))
        else:
            path = path_template
        
        full_path = self.docs_root / path / filename
        
        self.logger.info(f"Generated filename: {filename} at {path}")
        
        return {
            'filename': filename,
            'template': template,
            'path': path,
            'full_path': str(full_path),
            'needs_suffix': rule.get('needs_suffix', False),
            'safe_title': safe_title
        }
    
    def _slugify(self, text: str) -> str:
        """텍스트를 파일명으로 안전하게 변환"""
        # Unicode 정규화
        text = unicodedata.normalize('NFKC', text)
        # 공백을 하이픈으로
        text = re.sub(r'\s+', '-', text)
        # 파일명에 안전하지 않은 문자 제거
        text = re.sub(r'[^\w\-가-힣ㄱ-ㅎㅏ-ㅣ]', '', text)
        # 연속된 하이픈 제거
        text = re.sub(r'-+', '-', text)
        # 앞뒤 하이픈 제거
        text = text.strip('-')
        return text or 'untitled'
    
    def _find_next_suffix(self, scenario: str, date: str, title: str, template: str) -> str:
        """suffix 자동 증가 - 템플릿 기반"""
        rule = self.config['scenarios'][scenario]
        path = self.docs_root / rule['path']
        
        if not path.exists():
            self.logger.debug(f"Path does not exist, using suffix 'a': {path}")
            return 'a'
        
        suffix_chars = self.config.get('suffix', {}).get('chars', 'abcdefghij')
        
        # 템플릿에서 suffix 위치 찾기
        for suffix in suffix_chars:
            # 템플릿 기반으로 테스트 파일명 생성
            test_params = {'date': date, 'title': title, 'suffix': suffix}
            try:
                test_name = template.format(**test_params)
            except KeyError:
                # 템플릿 파싱 실패 시 기본 패턴 사용
                test_name = f"개념-{date}{suffix}-{title}.md"
                self.logger.warning(f"Template parsing failed, using default pattern: {test_name}")
            
            if not (path / test_name).exists():
                self.logger.debug(f"Found available suffix: {suffix}")
                return suffix
        
        # 모든 suffix가 사용된 경우
        self.logger.warning(f"All suffixes used for {date}-{title}, using 'z'")
        return 'z'
    
    def get_specs(self, scenario: str) -> Dict[str, Any]:
        """필요한 spec 파일 목록 반환"""
        if scenario not in self.config['scenarios']:
            return {'error': f'Unknown scenario: {scenario}'}
        
        spec_files = self.config['scenarios'][scenario].get('spec_files', [])
        full_paths = [str(self.docs_root / '90-설정' / 'specs' / f) for f in spec_files]
        
        return {
            'spec_files': spec_files,
            'full_paths': full_paths
        }
    
    def validate(self, filepath: str, mode: str = 'deep') -> Dict[str, Any]:
        """
        파일 검증 - 기본이 deep validation
        
        mode='deep' (기본): 구조 검증 + validator specs 반환
        mode='quick': 구조 검증만
        """
        path = Path(filepath)
        
        if not path.exists():
            return {'status': 'error', 'error': 'File not found'}
        
        # 기본 구조 검증
        checks = {
            'exists': True,
            'has_frontmatter': False,
            'has_title': False,
            'has_type': False,
            'has_created': False
        }
        
        warnings = []
        errors = []
        
        try:
            content = path.read_text(encoding='utf-8')
        except Exception as e:
            return {'status': 'error', 'error': f'Cannot read file: {e}'}
        
        # Frontmatter 검증
        match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if match:
            checks['has_frontmatter'] = True
            try:
                frontmatter = yaml.safe_load(match.group(1))
                
                # 필수 필드 검증
                if 'title' in frontmatter:
                    checks['has_title'] = True
                else:
                    errors.append("Missing 'title' field")
                
                if 'type' in frontmatter:
                    checks['has_type'] = True
                else:
                    errors.append("Missing 'type' field")
                
                if 'created' in frontmatter:
                    checks['has_created'] = True
                else:
                    warnings.append("Missing 'created' field")
                
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML frontmatter: {e}")
        else:
            errors.append("No frontmatter found")
        
        # 상태 결정
        if errors:
            status = 'error'
        elif warnings:
            status = 'warning'
        else:
            status = 'success'
        
        result = {
            'status': status,
            'checks': checks,
            'errors': errors,
            'warnings': warnings
        }
        
        # Deep validation 모드
        if mode == 'deep' and match:
            # Validator specs 경로 추가
            validator_specs = [
                str(self.docs_root / '90-설정' / 'specs' / 'validators' / 'link-validator.spec.md'),
                str(self.docs_root / '90-설정' / 'specs' / 'validators' / 'tag-validator.spec.md')
            ]
            
            # 링크 분석
            links_by_type = {
                'moc': [],
                'concept': [],
                'literature': [],
                'source': []
            }
            
            # MOC 링크
            moc_links = re.findall(r'\[\[맵-([^\]]+)\]\]', content)
            links_by_type['moc'] = [f"맵-{m}" for m in moc_links]
            
            # 개념 링크
            concept_links = re.findall(r'\[\[개념-([^\]]+)\]\]', content)
            links_by_type['concept'] = [f"개념-{c}" for c in concept_links]
            
            # 자료정리 링크
            lit_links = re.findall(r'\[\[정리-([^\]]+)\]\]', content)
            links_by_type['literature'] = [f"정리-{l}" for l in lit_links]
            
            # source 필드
            if frontmatter and 'source' in frontmatter:
                source = frontmatter['source']
                if isinstance(source, str) and source.startswith('[[') and source.endswith(']]'):
                    links_by_type['source'] = [source[2:-2]]
            
            result['deep'] = {
                'validator_specs': validator_specs,
                'context': {
                    'frontmatter': frontmatter if match else {},
                    'link_analysis': {
                        'by_type': {k: len(v) for k, v in links_by_type.items()},
                        'links': links_by_type
                    }
                }
            }
            
            # 타입별 검증 규칙 적용
            file_type = frontmatter.get('type') if match and frontmatter else None
            if file_type == 'permanent':
                if not links_by_type['moc']:
                    warnings.append("권장: MOC 링크 추가")
                if len(links_by_type['concept']) < 2:
                    warnings.append("권장: 관련 개념 2개 이상 연결")
        
        # 경고/에러 업데이트
        result['warnings'] = warnings
        result['errors'] = errors
        
        return result
    
    def list_mocs(self) -> Dict[str, Any]:
        """MOC 목록 반환"""
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
                
                match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
                if match:
                    frontmatter = yaml.safe_load(match.group(1))
                    tags = frontmatter.get('tags', [])
                else:
                    tags = []
                
                title = file_path.stem.replace('맵-', '')
                concept_links = re.findall(r'\[\[개념-[^\]]+\]\]', content)
                
                mocs.append({
                    'filename': file_path.name,
                    'title': title,
                    'path': str(file_path.relative_to(self.docs_root)),
                    'full_path': str(file_path),
                    'tags': tags,
                    'linked_concepts': len(concept_links)
                })
            except Exception:
                continue
        
        return {
            'mocs': mocs,
            'count': len(mocs)
        }
    
    def list_concepts(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """개념 목록 반환"""
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
                    created = frontmatter.get('created')
                else:
                    tags = []
                    created = None
                
                # 필터 적용
                if tag_filters:
                    if not any(tag in tags for tag in tag_filters):
                        continue
                
                if after_date and created:
                    if hasattr(created, 'strftime'):
                        created_str = created.strftime('%Y-%m-%d')
                    else:
                        created_str = str(created)
                    if created_str < after_date:
                        continue
                
                # MOC 링크 찾기
                moc_links = re.findall(r'\[\[맵-[^\]]+\]\]', content)
                
                concepts.append({
                    'filename': file_path.name,
                    'title': file_path.stem.replace('개념-', ''),
                    'path': str(file_path.relative_to(self.docs_root)),
                    'full_path': str(file_path),
                    'tags': tags,
                    'created': created.strftime('%Y-%m-%d') if hasattr(created, 'strftime') else str(created),
                    'moc_links': len(moc_links)
                })
            except Exception:
                continue
        
        return {
            'concepts': concepts,
            'count': len(concepts)
        }
    
    def get_file_preview(self, filepath: str, lines: int = 5) -> Dict[str, Any]:
        """파일 미리보기"""
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
        
        match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
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
        
        body_lines = body.strip().split('\n')
        preview_lines = body_lines[:lines]
        preview = '\n'.join(preview_lines)
        
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
            'commands': ['scenario_info', 'filename', 'specs', 'validate', 'list_mocs', 'list_concepts', 'preview']
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
    
    if command == 'scenario_info':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: orchestrator.py scenario_info <scenario>'}))
            sys.exit(1)
        
        scenario = sys.argv[2]
        result = helper.get_scenario_info(scenario)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'filename':
        if len(sys.argv) < 4:
            print(json.dumps({'error': 'Usage: orchestrator.py filename <scenario> <title>'}))
            sys.exit(1)
        
        scenario = sys.argv[2]
        title = sys.argv[3]
        result = helper.get_filename(scenario, title)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'specs':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: orchestrator.py specs <scenario>'}))
            sys.exit(1)
        
        scenario = sys.argv[2]
        result = helper.get_specs(scenario)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'validate':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: orchestrator.py validate <filepath> [mode]'}))
            sys.exit(1)
        
        filepath = sys.argv[2]
        mode = sys.argv[3] if len(sys.argv) > 3 else 'deep'
        result = helper.validate(filepath, mode)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'list_mocs':
        result = helper.list_mocs()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'list_concepts':
        filters = {}
        if len(sys.argv) > 2:
            try:
                filters = json.loads(sys.argv[2])
            except json.JSONDecodeError:
                pass
        
        result = helper.list_concepts(filters)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'preview':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: orchestrator.py preview <filepath> [lines]'}))
            sys.exit(1)
        
        filepath = sys.argv[2]
        lines = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        result = helper.get_file_preview(filepath, lines)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        print(json.dumps({'error': f'Unknown command: {command}'}))
        sys.exit(1)


if __name__ == '__main__':
    main()