# Python-PPTX Hard Rules (Short Core)

这些规则用于避免报错和结构性排版事故。执行时优先级最高。

## A. API 与导入约束

1. 只用公共枚举导入：
   - `from pptx.enum.shapes import MSO_SHAPE`
   - `from pptx.enum.dml import MSO_LINE`
   - `from pptx.enum.text import PP_ALIGN, MSO_ANCHOR`
2. 禁止导入内部路径（例如 `pptx.shapes.autoshape`）。
3. 属性名只用官方写法：
   - 填充色：`shape.fill.fore_color.rgb`
   - 边框色：`shape.line.color.rgb`
   - 去边框：`shape.line.fill.background()`
   - 字体名：`font.name`
   - 垂直对齐：`text_frame.vertical_anchor`
   - 水平对齐：`paragraph.alignment`

## B. 防御式初始化

4. 设置填充色前必须 `shape.fill.solid()`。
5. 无填充必须 `shape.fill.background()`。
6. 文本自动换行前必须设 `text_frame.word_wrap = True`。
7. 向现有文本框写多段文本前，先 `text_frame.clear()`。

## C. 强类型与画布

8. 颜色必须使用 `RGBColor(r, g, b)`，禁止 `#hex` 字符串。
9. 坐标和尺寸必须使用 `Inches()` / `Pt()`，禁止字符串单位。
10. 标准 16:9 画布使用：
    - `prs.slide_width = Inches(10)`
    - `prs.slide_height = Inches(5.625)`

## D. 文本与图层安全

11. 复杂排版遵循 Shape -> TextFrame -> Paragraph -> Run 分层，不跨级改样式。
12. 复杂图形场景使用“形文分离”：形状画底，透明 textbox 承载文字。
13. 左右同一行信息使用两个 textbox，Y 和高度相同，分别左/右对齐。
14. 图层冲突时，使用 `_spTree.append(shape._element)` 置顶。

## E. 工程化稳定性

15. 并排卡片/网格必须使用公式计算，禁止硬编码逐个微调。
16. 文件输出建议使用时间戳文件名，避免占用冲突。
