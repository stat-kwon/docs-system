#!/usr/bin/env python3
"""
Zettelkasten 도우미 v3 - 환경 독립성과 강화된 에러 처리

주요 변경사항:
- 환경 변수 기반 경로 설정 (DOCS_HOME)
- 통합 로깅 시스템
- 시나리오별 검증 로직
- 개선된 파일명 생성 (슬러그화)
- 유연한 프런트매터 파싱
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
    """경량 도우미 클래스 - 환경 독립적 버전"""
    
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
    
    def match_scenario(self, user_input: str) -> Dict[str, Any]:
        """시나리오 매칭 - 단순 버전 (하위 호환성)"""
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
        
        # 매칭 실패시 기본 시나리오 반환
        return {
            'scenario': 'search',  # 기본값을 None에서 'search'로 변경
            'config': self.config['scenarios'].get('search', {}),
            'spec_files': self.config['scenarios'].get('search', {}).get('spec_files', []),
            'path': '',
            'auto_execute': False,
            'validation': [],
            'fallback': True,
            'message': 'No exact match found, defaulting to search'
        }
    
    def match_scenario_advanced(self, user_input: str) -> Dict[str, Any]:
        """
        고급 시나리오 매칭 - 가중치 기반 점수 계산
        Claude Desktop이 최종 판단할 수 있도록 상세 정보 제공
        """
        user_input_lower = user_input.lower()
        scenario_scores = {}
        
        # 각 시나리오별 점수 계산
        for scenario_name, scenario_config in self.config['scenarios'].items():
            score = 0
            matched_keywords = []
            
            keywords = scenario_config.get('keywords', [])
            weights = scenario_config.get('keyword_weights', {})
            
            for keyword in keywords:
                if keyword in user_input_lower:
                    # 기본 점수 1점, 가중치가 있으면 적용
                    keyword_weight = weights.get(keyword, 1.0)
                    score += keyword_weight
                    matched_keywords.append(keyword)
                    
                    # 키워드 위치에 따른 추가 점수 (앞쪽일수록 높음)
                    position = user_input_lower.find(keyword)
                    position_bonus = (1 - position / len(user_input_lower)) * 0.5 if position >= 0 else 0
                    score += position_bonus
            
            if score > 0:
                scenario_scores[scenario_name] = {
                    'score': score,
                    'matched_keywords': matched_keywords,
                    'keyword_count': len(matched_keywords),
                    'config': scenario_config
                }
        
        # 점수순 정렬
        sorted_scenarios = sorted(
            scenario_scores.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        # 결과 구성
        if sorted_scenarios:
            primary = sorted_scenarios[0]
            alternatives = [s[0] for s in sorted_scenarios[1:3]]  # 상위 2-3개 대안
            
            # 신뢰도 계산 (최고 점수와 다음 점수의 차이)
            confidence = 1.0
            if len(sorted_scenarios) > 1:
                score_diff = primary[1]['score'] - sorted_scenarios[1][1]['score']
                max_score = primary[1]['score']
                confidence = min(0.95, 0.5 + (score_diff / max_score * 0.45)) if max_score > 0 else 0.5
            
            return {
                'primary_scenario': primary[0],
                'confidence': round(confidence, 2),
                'score': primary[1]['score'],
                'matched_keywords': primary[1]['matched_keywords'],
                'alternatives': alternatives,
                'all_scores': {k: v['score'] for k, v in scenario_scores.items()},
                'reasoning': self._generate_reasoning(primary[0], primary[1]['matched_keywords'], confidence),
                'spec_files': primary[1]['config'].get('spec_files', []),
                'config': primary[1]['config'],
                'default_fallback': 'search'
            }
        else:
            # 매칭 실패시 기본값과 함께 상세 정보 제공
            return {
                'primary_scenario': 'search',
                'confidence': 0.0,
                'score': 0,
                'matched_keywords': [],
                'alternatives': [],
                'all_scores': {},
                'reasoning': 'No keywords matched. Using default search scenario.',
                'spec_files': self.config['scenarios'].get('search', {}).get('spec_files', []),
                'config': self.config['scenarios'].get('search', {}),
                'default_fallback': 'search',
                'is_fallback': True
            }
    
    def _generate_reasoning(self, scenario: str, keywords: List[str], confidence: float) -> str:
        """매칭 이유 생성"""
        if confidence > 0.8:
            strength = "강한"
        elif confidence > 0.5:
            strength = "중간"
        else:
            strength = "약한"
        
        return f"{strength} 일치 - 키워드 {', '.join(keywords)} 발견"
    
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
        mode='quick': 구조 검증만 (빠른 체크)
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
        
        # 구조적 검증 (rules.yaml 기반)
        validation_config = self.config.get('validation', {})
        
        # source_chain 검증
        if validation_config.get('source_chain') == 'required':
            if 'source' not in frontmatter or not frontmatter['source']:
                errors.append('Missing required field: source')
        
        # MOC 링크 검증
        moc_links = re.findall(r'\[\[맵-[^\]]+\]\]', content)
        moc_link_min = validation_config.get('moc_link_min', 0)
        if moc_link_min > 0 and len(moc_links) < moc_link_min:
            warnings.append(
                f'권장: MOC 링크 {moc_link_min}개 이상 추가 (현재 {len(moc_links)}개)'
            )
        
        # 개념 링크 검증
        concept_links = re.findall(r'\[\[개념-[^\]]+\]\]', content)
        concept_link_min = validation_config.get('concept_link_min', 0)
        if concept_link_min > 0 and len(concept_links) < concept_link_min:
            warnings.append(
                f'권장: 개념 링크 {concept_link_min}개 이상 추가 (현재 {len(concept_links)}개)'
            )
        
        # 태그 검증
        if 'tags' not in frontmatter or not frontmatter['tags']:
            warnings.append('권장: tags 필드 추가')
        
        # 기본 결과 구성
        result = {
            'status': 'success' if not errors else 'error',
            'errors': errors,
            'warnings': warnings,
            'checks': {
                'has_frontmatter': True,
                'has_source': 'source' in frontmatter,
                'has_tags': bool(frontmatter.get('tags')),
                'moc_links': len(moc_links),
                'concept_links': len(concept_links),
                'file_size': len(content),
                'line_count': content.count('\n')
            }
        }
        
        # Deep validation: validator specs와 context 추가
        if mode == 'deep':
            file_type = self._detect_file_type(path)
            validator_specs = self._get_relevant_validators(file_type)
            
            # 모든 링크 추출 및 분류
            all_links = re.findall(r'\[\[([^\]]+)\]\]', content)
            link_types = {
                'moc': [l for l in all_links if l.startswith('맵-')],
                'concept': [l for l in all_links if l.startswith('개념-')],
                'literature': [l for l in all_links if l.startswith('정리-')],
                'fleeting': [l for l in all_links if re.match(r'\d{8}-\d{4}', l)],
                'other': [l for l in all_links if not any([
                    l.startswith('맵-'),
                    l.startswith('개념-'),
                    l.startswith('정리-'),
                    re.match(r'\d{8}-\d{4}', l)
                ])]
            }
            
            # Frontmatter의 date 객체를 문자열로 변환
            serializable_frontmatter = {}
            for key, value in frontmatter.items():
                if hasattr(value, 'strftime'):
                    serializable_frontmatter[key] = value.strftime('%Y-%m-%d')
                elif isinstance(value, list):
                    serializable_frontmatter[key] = value
                else:
                    serializable_frontmatter[key] = str(value) if value is not None else None
            
            result['deep'] = {
                'file_type': file_type,
                'validator_specs': validator_specs,
                'context': {
                    'filepath': str(path),
                    'filename': path.name,
                    'relative_path': str(path.relative_to(self.docs_root)),
                    'frontmatter': serializable_frontmatter,
                    'link_analysis': {
                        'total': len(all_links),
                        'by_type': {k: len(v) for k, v in link_types.items()},
                        'links': link_types
                    }
                },
                'suggestions_enabled': True  # Claude가 MOC/개념 제안 가능
            }
        
        return result
    
    def _detect_file_type(self, path: Path) -> str:
        """파일명 패턴으로 타입 감지"""
        name = path.name
        if name.startswith('개념-'):
            return 'concept'
        elif name.startswith('정리-'):
            return 'literature'
        elif name.startswith('맵-'):
            return 'moc'
        elif name == '_index.md':
            return 'project'
        elif re.match(r'\d{8}-\d{4}', name):
            return 'fleeting'
        else:
            return 'unknown'
    
    def _get_relevant_validators(self, file_type: str) -> List[str]:
        """파일 타입별 관련 validator spec 반환"""
        validators_dir = self.docs_root / '90-설정' / 'specs' / 'validators'
        
        if not validators_dir.exists():
            return []
        
        # 모든 파일에 공통 적용
        specs = []
        
        # link-validator는 모든 파일에 적용
        link_validator = validators_dir / 'link-validator.spec.md'
        if link_validator.exists():
            specs.append(str(link_validator))
        
        # priority는 참고용
        priority = validators_dir / 'priority.spec.md'
        if priority.exists():
            specs.append(str(priority))
        
        # 타입별 추가 validator (향후 확장)
        # type_validator = validators_dir / f'{file_type}-validator.spec.md'
        # if type_validator.exists():
        #     specs.append(str(type_validator))
        
        return specs
    
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
                
                match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
                if match:
                    frontmatter = yaml.safe_load(match.group(1))
                    tags = frontmatter.get('tags', [])
                    created = frontmatter.get('created')
                    if created:
                        if hasattr(created, 'strftime'):
                            created = created.strftime('%Y-%m-%d')
                        elif not isinstance(created, str):
                            created = str(created)
                    else:
                        created = None
                else:
                    tags = []
                    created = None
                
                # 날짜 비교 개선 - None 처리 및 형식 검증
                if after_date and created:
                    try:
                        # 날짜 문자열 검증
                        if re.match(r'^\d{4}-\d{2}-\d{2}$', after_date) and re.match(r'^\d{4}-\d{2}-\d{2}$', created):
                            if created < after_date:
                                continue
                    except Exception as e:
                        self.logger.warning(f"Date comparison failed: {e}")
                        continue
                
                if tag_filters:
                    if not any(tag in tags for tag in tag_filters):
                        continue
                
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
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: orchestrator.py match <user_input>'}))
            sys.exit(1)
        
        user_input = sys.argv[2]
        result = helper.match_scenario(user_input)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'match_advanced':
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: orchestrator.py match_advanced <user_input>'}))
            sys.exit(1)
        
        user_input = sys.argv[2]
        result = helper.match_scenario_advanced(user_input)
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
        # python3 orchestrator.py validate /path/to/file.md          → deep (기본)
        # python3 orchestrator.py validate /path/to/file.md --quick  → quick
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Usage: orchestrator.py validate <filepath> [--quick]'}))
            sys.exit(1)
        
        filepath = sys.argv[2]
        mode = 'quick' if '--quick' in sys.argv else 'deep'
        
        result = helper.validate(filepath, mode=mode)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'list_mocs':
        result = helper.list_mocs()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == 'list_concepts':
        filters = None
        if len(sys.argv) > 2:
            try:
                filters = json.loads(sys.argv[2])
            except:
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
        print(json.dumps({
            'error': f'Unknown command: {command}',
            'available': ['match', 'filename', 'specs', 'validate', 'list_mocs', 'list_concepts', 'preview']
        }))
        sys.exit(1)


if __name__ == '__main__':
    main()
