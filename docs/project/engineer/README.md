# Engineer Work Logs (工程师工作日志)

## 📝 用途 (Purpose)
本目录存放所有 Engineer 角色的任务实现日志，作为开发过程的**落盘化记录**。

## 🎯 核心价值 (Why This Matters)
1. **知识传承**: 后续 Engineer 可查阅前人的实现思路与踩坑经验
2. **问题溯源**: 出现 Bug 时可追溯当时的设计决策
3. **AI 上下文**: Claude 可读取这些日志，避免重复犯错
4. **代码审查**: Architect/PM 通过日志 Review 实现质量

## 📋 使用规范 (Workflow)

### 1. 开始任务前
```bash
# 复制模板
cp template.md task-{编号}-{描述}.md

# 例如：
cp template.md task-1.2-dumper.md
```

### 2. 实现过程中
- ✍️ 实时记录关键决策和遇到的问题
- 🔍 如果卡住，先翻阅相关任务的 Engineer Log
- 💡 发现通用问题时，考虑更新 `doc3-spec.md`

### 3. 任务完成后
- ✅ 填写完整的测试结果
- 📦 列出所有产出文件
- 🚩 标注遗留问题（如果有）
- 🔄 更新状态为 `🟢 Completed`

## 📚 文件命名规范 (Naming Convention)

| 类型 | 格式 | 示例 |
|------|------|------|
| 常规任务 | `task-{编号}-{描述}.md` | `task-1.2-dumper.md` |
| Bug 修复 | `bugfix-{简述}.md` | `bugfix-uuid-collision.md` |
| 重构 | `refactor-{模块}.md` | `refactor-builder-api.md` |

## 🔍 已有日志 (Existing Logs)

### 任务日志 (Task Logs)

| 日志文件 | 任务 | 状态 | 日期 |
|---------|------|------|------|
| [task-1.2-1.3-shortcut-tool.md](./task-1.2-1.3-shortcut-tool.md) | 实现 decode/encode 工具，支持 AEA 格式 | 🟢 Completed | 2026-02-16 |
| [task-1.4-signing-solution.md](./task-1.4-signing-solution.md) | 发现并使用官方签名工具，验证 iPhone 导入 | 🟢 Completed | 2026-02-16 |

### 问题追踪 (Issue Tracking)

| 问题文件 | 描述 | 状态 | 日期 |
|---------|------|------|------|
| [issue-unsigned-import-blocked.md](./issue-unsigned-import-blocked.md) | 未签名文件无法导入问题及解决方案 | ✅ Resolved | 2026-02-16 |

---

**提醒**: 这不是可选项，是 **Iron Rule #4** 的强制要求！
