---
name: sie-autoppt
description: >
  SIE 专属 AutoPPT 流程入口。复用本机 ppt-master 脚本引擎，快速完成从源内容到可编辑 PPTX 的生产，并固化 SIE 风格规范。
---

# SIE AutoPPT Skill (Route A)

## 目标

- 使用 `ppt-master` 成熟流水线快速产出
- 在策略阶段强制执行 SIE 设计规则
- 逐步沉淀 SIE 模板资产，减少返工
- 支持 HTML 参考复刻并进行 PPT 化重构

## 引擎路径

- `PPT_MASTER_DIR = C:\Users\1\Documents\Cursor\ppt-master`

所有脚本调用均复用：

- `project_manager.py`
- `pdf_to_md.py` / `doc_to_md.py` / `web_to_md.py`
- `total_md_split.py` / `finalize_svg.py` / `svg_to_pptx.py`

## 规则入口（必须按阶段加载）

- 硬规则：`rules/python_pptx_hard_rules.md`
- HTML 复刻规则：`rules/html_to_ppt_rebuild.md`
- 页级质检：`checklists/page_qa_checklist.md`
- 模板生成规范：`references/template-driven-generation.md`
- 商务页型模式库：`references/business-slide-patterns.json`

执行要求：

1. 任何页面生成前，先加载硬规则。
2. 当输入为 HTML 或用户提出“复刻网页”时，额外加载 HTML 复刻规则。
3. 每轮生成后必须执行页级质检并形成修复闭环。
4. 当用户指定企业模板生成时，必须加载模板生成规范并按其页面角色执行。

## 输出路径与命名（全局强制）

1. 所有最终 PPT 一律输出到桌面：`%USERPROFILE%\Desktop`
2. 文件名必须包含时间戳，避免重名覆盖：
   - 推荐格式：`<业务名>_<YYYYMMDD_HHMMSS_mmm>.pptx`
3. 同一任务允许多次导出，但不得覆盖历史版本。

## 标准执行流

1. 源内容转换（如需要）
2. 项目初始化
3. 模板选择（可先无模板）
4. Strategist 八项确认（SIE风格约束）
5. Executor 逐页 SVG 生成
6. 后处理与导出

## HTML 复刻模式（新增）

触发条件：

- 用户输入 HTML 文件 / 网页 URL
- 用户明确要求“复刻”或“参考此网页做 PPT”

执行流程：

1. 将 HTML 转为可分析内容（`web_to_md.py` 或直接读取 HTML 结构摘要）。
2. 按 `rules/html_to_ppt_rebuild.md` 先做“元素映射与页级策略”。
3. 输出页级说明（页面目标、复刻来源、改造点、复刻/优化权重）。
4. 按页生成 SVG 与备注，执行页级 QA，至少完成一轮修复复检。
5. 执行导出脚本产出 PPTX。

## 模板驱动模式（SIE 固化）

触发条件：

- 用户提供模板路径（`.pptx`）
- 用户要求“首尾固定 + 中间按内容生成”

执行原则：

1. 固定页（欢迎页、感谢页）不改内容，仅保留位置。
2. 主题页只替换标题，颜色固定 `RGB(173, 5, 61)`。
3. 目录页按章节重复插入；仅当前章节红色高亮 `RGB(173,5,61)`，其余章节统一常规色 `RGB(184,196,201)`。
4. 正文页必须从空白正文母页克隆生成，不得复用历史示例页。
5. 生成顺序必须保证最后一页为感谢页。

## SIE 策略约束（默认）

1. 画幅：`ppt169`
2. 页数：`8-12` 页（首版）
3. 受众：管理层 + 业务负责人
4. 风格：高端咨询风 + 商务克制
5. 配色：主色深蓝，辅色灰，强调色低饱和青
6. 图标：线性图标优先，风格统一
7. 字体：标题与正文字体分层，正文可读性优先
8. 图片：业务实景/数据示意优先，避免装饰性空图

## 强制质量门禁

- 每页至少一个视觉锚点（图、图标、数据卡、流程图）
- 避免纯文字页
- 关键页（封面、目录、结尾）视觉风格必须一致
- 导出前必须完成：
  - `total_md_split.py`
  - `finalize_svg.py`
  - `svg_to_pptx.py -s final`

## 推荐使用方式

先让 AI 输出：

- `design_spec.md`（先确认，再执行）
- `svg_output/` 全量页面
- `notes/total.md`
- HTML 复刻场景需追加 `html_mapping.md`（可放项目根目录）

最后再运行脚本导出 PPTX。
