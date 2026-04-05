# HTML Input Spec

The HTML input path now supports two compatible modes:

1. Legacy structured blocks built from `phase-*`, `scenario`, and `note`
2. Explicit slide pages built from `<slide data-pattern="...">`

If both are present, the planner prioritizes `<slide>` pages.

## Recommended `<slide>` format

```html
<div class="title">Supply Chain Compliance Program</div>
<div class="subtitle">Executive update for steering committee</div>

<slide data-pattern="general_business">
  <h2>Global regulation trend</h2>
  <ul>
    <li>GDPR and cross-border data controls</li>
    <li>Supply-chain due diligence requirements</li>
  </ul>
</slide>

<slide data-pattern="process_flow">
  <h2>Implementation roadmap</h2>
  <p class="subtitle">Four coordinated steps</p>
  <ul>
    <li>Assess</li>
    <li>Design</li>
    <li>Launch</li>
    <li>Operate</li>
  </ul>
</slide>

<slide data-pattern="solution_architecture">
  <h2>Target architecture</h2>
  <p>Data layer</p>
  <p>Application layer</p>
  <p>Governance layer</p>
</slide>

<div class="footer">Thanks</div>
```

Rules:

- Each `<slide>` becomes one body page.
- `data-pattern` is optional. If omitted, the planner infers a suitable pattern.
- Supported native render patterns include:
  - `general_business`
  - `process_flow`
  - `solution_architecture`
  - `org_governance`
  - `comparison_upgrade`
  - `capability_ring`
  - `five_phase_path`
  - `pain_cards`
- Slide content can come from either:
  - `<ul><li>...</li></ul>`
  - plain `<p>` / `<div>` text inside the slide

## Legacy block format

Legacy input is still supported for backward compatibility.

Minimum usable content:

- at least one `phase-*` group, or
- at least one `scenario`, or
- at least one `note`

Important fields:

- `title`
  - used for the cover and the first page title
- `subtitle`
  - used for the first page subtitle
- `footer`
  - used as supporting text on the focus/governance page
- `phase-time`
- `phase-name`
- `phase-code`
- `phase-func`
- `phase-owner`
- `scenario`
- `note`

Example:

```html
<div class="title">项目概览与 UAT 阶段规划</div>
<div class="subtitle">按阶段推进测试执行，验证核心链路并明确责任边界。</div>

<div class="phase-time">4/7-4/8</div>
<div class="phase-name">基础配置</div>
<div class="phase-code">BC-1 ~ BC-5</div>
<div class="phase-func">核心功能：类别管理 / 实体管理 / 文件类型 / 链路配置</div>
<div class="phase-owner">责任人：韩新宇、魏海明</div>

<div class="scenario">基础配置模块（BC）</div>
<div class="scenario">数据查询验证（DQ / ID）</div>

<div class="note">配置是否支持业务快速启动，并可定位异常。</div>
<div class="note">数据与文件链路是否可追溯，关键节点可回放。</div>

<div class="footer">验证目标：确保追溯链路在真实业务场景下稳定运行并形成闭环。</div>
```

## Page-count behavior

- `plan` / `make` no longer force HTML input down to three body pages.
- If `--chapters` is omitted:
  - legacy HTML keeps all detected legacy sections, up to what the planner can derive
  - `<slide>` HTML keeps all detected slide tags
- If `--chapters N` is provided, the planner caps body pages at `N`.
- The bundled default template currently ships with a 20-pair preallocated slide pool.

## Notes

- The directory slide shows a rolling five-item window when the deck has more than five body pages.
- Legacy input remains useful for old samples in `input/`.
- For richer layouts, prefer explicit `<slide data-pattern>` input.
