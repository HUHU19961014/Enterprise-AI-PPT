# SIE AutoPPT

`SIE-autoppt` 是一个基于企业模板的 PPT 自动生成项目，当前做法是：

- 从 HTML 输入中提取标题、阶段、场景和关注点。
- 按模板页角色填充封面主题、目录页和正文页。
- 根据语义关键词自动挑选版式模式。
- 产出原生 `.pptx`，并同步生成 QA 报告。

## 目录结构

```text
SIE-autoppt/
├─ assets/templates/          # 本地模板备份与模板指纹
├─ input/                     # HTML 输入样例
├─ projects/generated/        # 默认输出目录（建议加入 .gitignore）
├─ skills/sie-autoppt/        # 项目内约束、规则和参考资料
├─ tools/sie_autoppt/         # 模块化生成逻辑
├─ run_sie_autoppt.ps1        # 一键生成入口
└─ tools/regression_check.ps1 # 回归检查入口
```

## 快速开始

```powershell
python .\tools\sie_autoppt_cli.py `
  --template .\assets\templates\sie_template.pptx `
  --html .\input\uat_plan_sample.html `
  --output-name SIE_AutoPPT `
  --output-dir .\projects\generated `
  --chapters 3 `
  --active-start 0
```

也可以直接执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_sie_autoppt.ps1
```

## 当前实现思路

1. 模板页索引由 `tools/sie_autoppt/config.py` 统一管理。
2. HTML 内容在 `tools/sie_autoppt/generator.py` 中解析并映射到三类正文页。
3. 模式识别配置位于 `skills/sie-autoppt/references/business-slide-patterns.json`。
4. QA 检查会输出结束页、目录页和潜在文本溢出风险。

## 模板指纹

替换模板后建议立刻更新指纹：

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\update_template_version.ps1
```

## 回归检查

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\regression_check.ps1
```

## 版本管理建议

建议尽快启用 Git。这个项目已经包含模板、脚本、样例输入和规则文件，多次调整版式与文案时非常容易“改对了但回不去”。至少建议做这三件事：

1. 在项目根目录执行 `git init`。
2. 先提交一版可运行基线。
3. 之后每次改模板、改规则、改生成逻辑分开提交。
