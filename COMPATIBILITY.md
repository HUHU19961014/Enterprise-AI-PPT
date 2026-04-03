# Compatibility & Upgrade Policy

本文档用于管理 `SIE-autoppt` 与外部 `ppt-master` 的兼容关系，避免“上游更新后本地流程失效”。

## 1. 当前架构边界

- **外部依赖层（会受上游更新影响）**
  - `C:\Users\1\Documents\Cursor\ppt-master\skills\ppt-master\scripts\*`
- **本地固化层（不受上游自动影响）**
  - `skills/sie-autoppt/*`
  - `tools/template_poc_generate.py`
  - `docs/*`

## 2. 已验证基线

- 外部依赖路径：`C:\Users\1\Documents\Cursor\ppt-master`
- 本地模板备份：`assets/templates/sie_template.pptx`（优先使用本地副本）
- 验证日期：`2026-04-02`
- 验证能力：
  - 模板驱动生成（首尾固定、中间自动生成）
  - 目录重复 + 当前章节高亮
  - 正文母页克隆
  - 桌面时间戳输出

> 每次 `ppt-master` 更新后，必须重新跑回归脚本并更新此文档的“验证日期”。

## 3. 升级策略

### A. 日常模式（推荐）

1. 更新 `ppt-master`
2. 执行 `tools/regression_check.ps1`
3. 若全部通过，更新“已验证基线”日期

### B. 稳定模式（强稳定）

- 将关键上游脚本镜像到 `SIE-autoppt/vendor/ppt-master/`
- 仅在人工审核后更新 vendor 版本

## 4. 回归通过标准

- [ ] 外部依赖路径存在且可访问
- [ ] Python 可运行且 `python-pptx` 可导入
- [ ] 模板文件存在
- [ ] `template_poc_generate.py` 语法通过
- [ ] 可成功生成一个桌面时间戳 PPT

## 5. 常见故障与处理

- **问题：上游脚本参数变更**
  - 处理：更新本仓库调用命令并记录到 README
- **问题：目录页图片丢失**
  - 处理：确认 COM 复制逻辑生效，不改为普通克隆
- **问题：章节高亮残留**
  - 处理：检查“先重置再高亮”是否执行
