# SIE AutoPPT Release Checklist

用于上线前 5-10 分钟快速检查，确保“能生成、可交付、可追溯”。

## 1) 环境检查

- [ ] Python 可用（`python --version`）
- [ ] `python-pptx` 可导入（`python -c "import pptx"`）
- [ ] PowerPoint 可正常打开（目录页图片修复依赖 COM）

## 2) 资产检查

- [ ] 本地模板存在：`assets/templates/sie_template.pptx`
- [ ] 模板指纹文件存在：`assets/templates/sie_template.version.txt`
- [ ] 若模板刚替换，已执行：
  - `powershell -ExecutionPolicy Bypass -File "tools/update_template_version.ps1"`

## 3) 回归检查（强制）

- [ ] 执行：
  - `powershell -ExecutionPolicy Bypass -File "tools/regression_check.ps1"`
- [ ] 结果为 `Regression check passed`

## 4) 生成检查

- [ ] 执行一键生成：
  - `powershell -ExecutionPolicy Bypass -File "run_sie_autoppt.ps1" -OutputName "赛意自动化_发布验证" -Chapters 3 -ActiveStart 0`
- [ ] 控制台出现：
  - `[OK] Template fingerprint matched.`
- [ ] 桌面成功生成两个文件：
  - `*.pptx`
  - `*_QA.txt`

## 5) 视觉验收（人工）

- [ ] 首页、主题页、感谢页位置正确且未被破坏
- [ ] 目录页重复出现，且仅当前章节为红色 `RGB(173,5,61)`
- [ ] 目录页右上角图片存在（第3/5/7页）
- [ ] 正文页由正文母页克隆（版式同构）
- [ ] 文本无明显溢出、遮挡、错位

## 6) 交付归档

- [ ] 记录本次模板指纹（`sha256`）
- [ ] 记录输出文件名（带时间戳）
- [ ] 若发现问题，更新：
  - `skills/sie-autoppt/references/template-driven-generation.md`
  - `COMPATIBILITY.md`

---

通过标准：以上所有项目均勾选通过，才可进入正式交付。
