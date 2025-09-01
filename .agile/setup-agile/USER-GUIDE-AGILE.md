# Agile Development User Guide with Claude Code CLI

## 📚 Overview
This guide explains how to use 4 context files and 10 command files for complete Agile workflow with Claude Code CLI.

---

## 📁 Part 1: Context Files (Project Information)

### 1. `.claude/context.md`
**Purpose**: Project overview and current state
**When to update**: 
- Project start (once)
- Major tech stack changes
- Sprint transitions

**Usage**:
```bash
# Claude reads this to understand your project
claude "Read .claude/context.md and tell me project status"
```

### 2. `.claude/conventions.md`
**Purpose**: Coding standards and rules
**When to update**:
- Project start (once)
- When team agrees on new standards
- Rarely changes

**Usage**:
```bash
# Reference when writing code
claude "Following conventions.md, implement login feature"
```

### 3. `.claude/current-sprint.md`
**Purpose**: Active sprint tracking
**When to update**:
- Daily (progress updates)
- When feature status changes
- When blockers appear

**Usage**:
```bash
# Check sprint progress
claude "Read current-sprint.md and show today's priorities"
```

### 4. `.agile/backlog/product-backlog.md`
**Purpose**: All features and user stories
**When to update**:
- Sprint planning (select stories)
- New feature requests
- After sprint review

**Usage**:
```bash
# Plan next sprint
claude "From product-backlog.md, select 21 points for next sprint"
```

---

## 📋 Part 2: Command Files (Actions)

### Sprint Management Commands

#### 1. `sprint-planning.md`
**When**: Monday, Week 1 of sprint
**Purpose**: Plan 2-week sprint
```bash
claude "$(cat .claude/commands/sprint-planning.md)"
# Selects ~21 points of features from backlog
```

#### 2. `create-worktrees.md`
**When**: After sprint planning
**Purpose**: Setup parallel development
```bash
claude "$(cat .claude/commands/create-worktrees.md) reports bulk-ops settings"
# Creates git worktrees for each feature
```

#### 3. `daily-standup.md`
**When**: Every morning 9:00 AM
**Purpose**: Check status and priorities
```bash
claude "$(cat .claude/commands/daily-standup.md)"
# Shows all worktrees status and today's focus
```

#### 4. `sprint-review.md`
**When**: Friday, Week 2 of sprint
**Purpose**: Demo and close sprint
```bash
claude "$(cat .claude/commands/sprint-review.md)"
# Calculates velocity and prepares demo
```

### Development Commands

#### 5. `develop-feature.md`
**When**: Starting new feature work
**Purpose**: TDD implementation
```bash
cd ../project-reports
claude "$(cat ../project/.claude/commands/develop-feature.md) reports"
# Writes tests first, then implements feature
```

#### 6. `test-feature.md`
**When**: After code changes
**Purpose**: Run all tests
```bash
claude "$(cat .claude/commands/test-feature.md) reports"
# Runs unit, E2E, and visual tests
```

#### 7. `merge-feature.md`
**When**: Feature complete with 90% coverage
**Purpose**: Merge to main
```bash
claude "$(cat .claude/commands/merge-feature.md) reports"
# Safely merges and cleans up worktree
```

### Maintenance Commands

#### 8. `fix-bug.md`
**When**: Bug reported
**Purpose**: TDD bug fixing
```bash
claude "$(cat .claude/commands/fix-bug.md) login-error"
# Reproduces bug, writes test, fixes code
```

#### 9. `update-docs.md`
**When**: After feature/fix complete
**Purpose**: Documentation
```bash
claude "$(cat .claude/commands/update-docs.md) reports"
# Updates README, API docs, changelog
```

### Workflow Command

#### 10. `daily-workflow.md`
**When**: Full day workflow guide
**Purpose**: Complete daily routine
```bash
claude "$(cat .claude/commands/daily-workflow.md)"
# Guides through entire day's tasks
```

---

## 🗓️ Part 3: Sprint Timeline (2 Weeks)

### Week 1

#### Monday - Sprint Start
```bash
# Morning
1. claude "$(cat .claude/commands/sprint-planning.md)"
2. claude "$(cat .claude/commands/create-worktrees.md) [features]"
3. Update .claude/current-sprint.md

# Afternoon
4. cd ../project-feature1
5. claude "$(cat .claude/commands/develop-feature.md) feature1"
```

#### Tuesday to Friday - Development
```bash
# Daily Routine
9:00  - claude "$(cat .claude/commands/daily-standup.md)"
9:30  - cd ../project-[feature]
        claude "$(cat .claude/commands/develop-feature.md) [feature]"
15:00 - claude "$(cat .claude/commands/test-feature.md) [feature]"
17:00 - Update .claude/current-sprint.md
```

### Week 2

#### Monday to Thursday - Complete & Test
```bash
# Focus on completion
- Complete remaining features
- Fix bugs: claude "$(cat .claude/commands/fix-bug.md)"
- Increase test coverage
- Start merging completed features
```

#### Friday - Sprint Close
```bash
# Morning
1. claude "$(cat .claude/commands/merge-feature.md)" for remaining features
2. claude "$(cat .claude/commands/update-docs.md)" for all changes

# Afternoon
3. claude "$(cat .claude/commands/sprint-review.md)"
4. Update .agile/backlog/product-backlog.md
5. Clear .claude/current-sprint.md for next sprint
```

---

## 📊 Part 4: Common Workflows

### Starting a New Feature
```bash
1. Check assignment in current-sprint.md
2. cd ../project-[feature]
3. claude "$(cat .claude/commands/develop-feature.md) [feature]"
4. Write tests first (TDD)
5. Implement code
6. claude "$(cat .claude/commands/test-feature.md) [feature]"
7. Achieve 90% coverage
8. claude "$(cat .claude/commands/merge-feature.md) [feature]"
```

### Daily Developer Flow
```bash
Morning:
- claude "$(cat .claude/commands/daily-standup.md)"
- Check blockers
- Pick priority feature

Development:
- Work in feature worktree
- Commit frequently
- Test regularly

Evening:
- Update progress
- Merge if ready
- Plan tomorrow
```

### Handling Bugs
```bash
1. Reproduce issue
2. cd to relevant worktree
3. claude "$(cat .claude/commands/fix-bug.md) [bug-description]"
4. Write failing test
5. Fix code
6. Verify all tests pass
7. Merge fix
```

---

## 🎯 Part 5: Best Practices

### File Updates Schedule

| File | Update Frequency | Who Updates |
|------|-----------------|-------------|
| context.md | Rarely | Tech Lead |
| conventions.md | Rarely | Team |
| current-sprint.md | Daily | Developer |
| product-backlog.md | Each Sprint | Product Owner |

### Command Usage Pattern

| Time | Command | Purpose |
|------|---------|---------|
| Sprint Start | sprint-planning, create-worktrees | Setup |
| Daily 9 AM | daily-standup | Status check |
| Daily Work | develop-feature, test-feature | Development |
| When Ready | merge-feature | Integration |
| Sprint End | sprint-review | Close sprint |

### Success Metrics
- ✅ 90% test coverage on all features
- ✅ ~21 story points per sprint
- ✅ Daily standups completed
- ✅ All features reviewed before merge
- ✅ Documentation always updated

---

## 🚀 Part 6: Quick Start

### First Time Setup
```bash
# 1. Create folder structure
mkdir -p .claude/commands .agile/backlog

# 2. Copy all context files to .claude/
# 3. Copy all command files to .claude/commands/
# 4. Edit context.md with your project info
# 5. Add user stories to product-backlog.md

# 6. Start first sprint
claude "$(cat .claude/commands/sprint-planning.md)"
```

### Daily Commands Cheatsheet
```bash
# Morning
alias standup='claude "$(cat .claude/commands/daily-standup.md)"'

# Development
alias develop='claude "$(cat .claude/commands/develop-feature.md)"'
alias test='claude "$(cat .claude/commands/test-feature.md)"'

# Integration
alias merge='claude "$(cat .claude/commands/merge-feature.md)"'

# Documentation
alias docs='claude "$(cat .claude/commands/update-docs.md)"'
```

---

## ⚠️ Important Notes

1. **Always update current-sprint.md daily** - This is your single source of truth
2. **Never skip tests** - 90% coverage is mandatory
3. **Follow conventions.md strictly** - Consistency matters
4. **Update docs immediately** - Not "later"
5. **Merge frequently** - Don't let features diverge

---

## 📞 Troubleshooting

| Problem | Solution |
|---------|----------|
| Low velocity | Review estimation in sprint retrospective |
| Failed tests | Never merge, fix first |
| Merge conflicts | Update feature branch with main first |
| Low coverage | Write more tests before proceeding |
| Blocked | Update current-sprint.md and escalate |

---

*This guide covers the complete Agile workflow. Follow the timeline and best practices for successful sprints!*