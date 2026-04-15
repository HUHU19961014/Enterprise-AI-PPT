# Host AI Brief Prompt Template (SIE One-page)

将以下业务材料整理为 **SIE 单页 PPT** 的 `brief.json`，用于渲染脚本：

目标要求：
1. 仅输出合法 JSON，不要输出解释文字。
2. 使用中文内容，字段名保持英文。
3. `layout_strategy` 默认填 `"auto"`。
4. 内容需覆盖：总体进度、关键待复核事项、上线前动作建议。
5. 保持可读性，避免长段堆叠。

JSON Schema（字段）：
- `title`: string
- `kicker`: string
- `summary_fragments`: [{ `text`: string, `bold`?: bool, `color`?: [r,g,b], `new_paragraph`?: bool }]
- `law_rows`: [{ `number`: string, `title`: string, `badge`: string, `badge_red`: bool, `runs`: [{ `text`: string, `bold`?: bool, `color`?: [r,g,b], `new_paragraph`?: bool }] }]
- `right_kicker`: string
- `right_title`: string
- `process_steps`: string[]
- `right_bullets`: [{ `label`: string, `body`: string }]
- `strategy_title`: string
- `strategy_fragments`: [{ `text`: string, `bold`?: bool, `color`?: [r,g,b], `new_paragraph`?: bool }]
- `footer`: string
- `page_no`: string
- `required_terms`: string[]
- `variant`: string（建议 `"auto"`）
- `layout_strategy`: string（建议 `"auto"`）
- `layout_overrides`?: object（AI 生成布局参数，可选）
  - `summary_y_offset`（建议 -520000 ~ -280000）
  - `hero_height`（建议 520000 ~ 680000）
  - `card_height`（建议 1400000 ~ 1650000）
  - `process_panel_height`（建议 1200000 ~ 1450000）
  - `strategy_height`（建议 380000 ~ 520000）
- `typography_overrides`?: object（AI 生成排版参数，可选）
  - `right_title_font_size`（建议 16.0 ~ 19.0）
  - `panel_title_font_size`（建议 14.6 ~ 16.2）
  - `bullet_font_size`（建议 10.0 ~ 11.2）

业务材料：
```text
{{在这里粘贴你的表格/清单原文}}
```

输出要求：
- 输出完整 `brief.json` 对象，可直接保存为 UTF-8 文件并用于渲染。
