---
created: 2024-10-24
updated: 2025-11-02
type: todo-dashboard
tags: [todo, tasks, dashboard]
---

# TODO List

## 📚 진행 중인 프로젝트

### Context Engineering Survey 학습
**상태**: 🟡 진행중 (23.1%) - Phase 1 완료! 🎉  
**상세**: [[20251102-1430-context-engineering-study-todo]]

```dataview
TABLE WITHOUT ID
  file.link as "섹션",
  length(filter(file.tasks, (t) => t.completed)) as "완료",
  length(filter(file.tasks, (t) => !t.completed)) as "미완료"
WHERE file = [[20251102-1430-context-engineering-study-todo]]
```

**빠른 진행**:
- [x] §1 Introduction ✅
- [x] §2 Related Work ✅
- [x] §3 Why Context Engineering ✅

**다음 단계**: Phase 2 - 핵심 구성요소
- [ ] §4.1 Context Retrieval & Generation ⬜

---

## 일반 Todo

```tasks
not done
path includes 10-수집/즉흥메모
group by filename
```

---

## 📊 통계

### 프로젝트 통계
```dataview
TABLE 
  length(filter(file.tasks, (t) => !t.completed)) as "미완료",
  length(filter(file.tasks, (t) => t.completed)) as "완료",
  round((length(filter(file.tasks, (t) => t.completed)) / length(file.tasks)) * 100, 1) + "%" as "진행률"
FROM "10-수집/즉흥메모"
WHERE file.name = "20251102-1430-context-engineering-study-todo"
```

### 전체 Todo 통계
```dataview
TABLE 
  length(filter(file.tasks, (t) => !t.completed)) as "미완료",
  length(filter(file.tasks, (t) => t.completed)) as "완료"
FROM "10-수집/즉흥메모"
WHERE file.frontmatter.type = "todo"
```

---

## 🎯 우선순위 작업

**오늘 할 일**:
1. ✅ Phase 1 완료! (§1-3)
2. 휴식 후 Phase 2 준비

**다음 목표**:
- Phase 2 시작 (§4 Core Components)
- 핵심개념 15개 목표 (CoT, RAG, Memory 등)

---

**최종 업데이트**: 2025-11-02 18:30
