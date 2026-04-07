# HTML 输入路径改进方案

> **版本**：v1.0  
> **创建日期**：2026-04-05  
> **状态**：待开发小组评估  
> **优先级**：P0（影响核心业务场景）

---

## 一、问题背景

### 当前状况

用户期望的工作流程：
```
AI 生成 HTML（15 页结构化内容）
    ↓
AI 复刻 HTML，形成 Python 代码
    ↓
使用企业模板渲染 PPT（固定首尾 + 复制空白页填充内容）
```

### 实际问题

1. **HTML 解析能力极度受限**
   - 只支持 `phase-*`、`scenario`、`note` 三类特定 class
   - 不支持 `<slide>` 标签、`data-pattern` 属性
   - 无法识别用户自定义的 15 页结构（封面、目录、背景、法规、痛点...）

2. **页面数量强制限制**
   - `MAX_BODY_CHAPTERS = 3` 硬编码
   - 无论 HTML 写多少页，最多生成 3 页正文
   - 加上封面/目录/结束页，总计不超过 6-7 页

3. **排版逻辑与 pattern 系统脱节**
   - HTML → PPTX 路径（`make` 命令）不使用 manifest.json 中的 8 种 pattern
   - 只有 DeckSpec JSON → PPTX 路径（`render` 命令）才使用 pattern
   - 导致用户无法利用 `general_business`、`process_flow` 等丰富布局

4. **与文档描述不符**
   - README 声称支持 "classic HTML -> PPTX rendering"
   - 实际实现仅支持特定的 3-4 页固定结构
   - 用户体验与预期差距巨大

---

## 二、改进目标

### 核心目标

让 HTML 输入路径支持：
1. ✅ 任意数量的 `<slide>` 标签（不再强制 3 页限制）
2. ✅ 每页指定 `data-pattern` 选择排版风格
3. ✅ 页面数量由内容驱动，支持用户指定范围

### 输入格式设计

```html
<!-- 封面 -->
<div class="title">供应链合规追溯体系建设方案</div>
<div class="subtitle">面向高管的合规风险防控方案</div>

<!-- 第 1 页：背景 -->
<slide data-pattern="overview">
  <h2>全球供应链监管趋势</h2>
  <ul>
    <li>2018 GDPR：数据隐私保护</li>
    <li>2023 德国供应链法：人权与环境保护</li>
  </ul>
</slide>

<!-- 第 2 页：法规解读 -->
<slide data-pattern="general_business">
  <h2>四大核心法规</h2>
  <p>GDPR、德国供应链法、CSRD、美国供应链透明度法案</p>
</slide>

<!-- 第 3-15 页：更多内容 -->
<slide data-pattern="process_flow">
  <h2>实施路线</h2>
  ...
</slide>

<slide data-pattern="solution_architecture">
  <h2>系统架构</h2>
  ...
</slide>

<!-- 结束页 -->
<div class="footer">谢谢</div>
```

---

## 三、技术方案

### 方案 A：扩展 HTML 解析器（推荐）

#### 3.1 修改 `deck_planner.py`

**当前逻辑：**
```python
# 只解析 phase-*, scenario, note
phases = parse_phase_elements(html_body)
scenarios = parse_scenarios(html_body)
notes = parse_notes(html_body)

# 强制限制最多 3 页
body_chapters = clamp_body_chapters(phases, scenarios, notes, max_chapters=3)
```

**改进后逻辑：**
```python
# 1. 优先解析 <slide> 标签
slides = parse_slide_elements(html_body)

if slides:
    # 路径 A：使用 <slide> 标签
    body_chapters = [
        BodyPageSpec(
            page_key=f"page_{i+1}",
            title=slide.title,
            subtitle=slide.subtitle,
            content_items=slide.content_items,
            pattern_id=slide.pattern_id or infer_pattern(slide),  # 使用 data-pattern 或自动推断
        )
        for i, slide in enumerate(slides)
    ]
else:
    # 路径 B：兼容旧的 phase-*, scenario, nate（保留向后兼容）
    phases = parse_phase_elements(html_body)
    scenarios = parse_scenarios(html_body)
    notes = parse_notes(html_body)
    body_chapters = clamp_body_chapters(phases, scenarios, notes, max_chapters=None)  # 移除硬上限
```

**新增函数：**
```python
def parse_slide_elements(soup: BeautifulSoup) -> list[SlideElement]:
    """解析 HTML 中的 <slide> 标签。"""
    slides = []
    for slide_elem in soup.find_all('slide'):
        # 提取 pattern
        pattern_id = slide_elem.get('data-pattern', None)
        
        # 提取标题
        title_elem = slide_elem.find('h2')
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # 提取副标题
        subtitle_elem = slide_elem.find('p', class_='subtitle')
        subtitle = subtitle_elem.get_text(strip=True) if subtitle_elem else ""
        
        # 提取内容（列表项或段落）
        content_items = []
        for li in slide_elem.find_all('li'):
            content_items.append(li.get_text(strip=True))
        
        slides.append(SlideElement(
            title=title,
            subtitle=subtitle,
            content_items=content_items,
            pattern_id=pattern_id,
        ))
    
    return slides
```

#### 3.2 修改 `config.py`

**当前代码：**
```python
MAX_BODY_CHAPTERS = 3
```

**改进后：**
```python
# 软上限：允许更多页数，但建议 AI 规划器合理控制
MAX_BODY_CHAPTERS = 20

# 新增：用户可通过 CLI 参数覆盖
DEFAULT_MIN_SLIDES = 3
DEFAULT_MAX_SLIDES = 20
```

#### 3.3 修改 `cli.py`

**新增参数：**
```python
@cli.command()
@click.option('--html', type=click.Path(exists=True), help='HTML 输入文件')
@click.option('--min-slides', type=int, default=None, help='最少幻灯片数（包括封面/目录/结束页）')
@click.option('--max-slides', type=int, default=None, help='最多幻灯片数')
def make(html, min_slides, max_slides):
    """HTML → PPTX 渲染。"""
    # 传递给规划器
    plan = plan_deck_from_html(html_path=html, min_slides=min_slides, max_slides=max_slides)
    ...
```

#### 3.4 修改 `deck_planner.py` 中的 `clamp_body_chapters()`

**当前代码：**
```python
def clamp_body_chapters(..., max_chapters=3):
    return chapters[:max_chapters]  # 强制截断
```

**改进后：**
```python
def clamp_body_chapters(..., max_chapters=None, min_chapters=None):
    """
    限制章节数量在用户指定范围内。
    
    Args:
        max_chapters: 最大章节数，None 表示不限制
        min_chapters: 最小章节数，None 表示不限制
    
    Returns:
        调整后的章节数量
    """
    if max_chapters is not None and len(chapters) > max_chapters:
        logger.warning(f"章节数量 {len(chapters)} 超过上限 {max_chapters}，截断处理")
        chapters = chapters[:max_chapters]
    
    if min_chapters is not None and len(chapters) < min_chapters:
        logger.warning(f"章节数量 {len(chapters)} 低于下限 {min_chapters}，建议补充内容")
    
    return chapters
```

#### 3.5 修改 `generator.py` 中的模板容量检查

**当前代码：**
```python
def validate_slide_pool_configuration(..., body_page_count: int):
    if len(body_pool) < body_page_count:
        raise ValueError("not enough preallocated slides")
```

**改进后：**
```python
def validate_slide_pool_configuration(..., body_page_count: int):
    if not manifest.slide_pools:
        # 没有 slide pool 的旧模板，使用动态克隆路径（已 deprecated 但保留兼容）
        logger.warning("模板未配置 slide_pools，使用 legacy clone 路径")
        return
    
    if len(body_pool) < body_page_count:
        raise ValueError(
            f"模板预分配的正文页数量不足：需要 {body_page_count} 页，"
            f"但模板只提供了 {len(body_pool)} 页。\n"
            f"请修改模板的 manifest.json，扩展 slide_pools.body 数组。"
        )
```

---

### 方案 B：直接使用 DeckSpec JSON（临时方案）

如果 HTML 解析器改进工作量较大，可先采用临时方案：

1. **AI 生成 DeckSpec JSON**（绕过 HTML）
2. **使用 `render` 命令渲染**

**优点：**
- 立即可用，无需修改 HTML 解析逻辑
- 完全支持 8 种 pattern
- 页面数量无限制

**缺点：**
- 不符合用户 "HTML → PPT" 的心理模型
- 需要修改 AI 规划逻辑

---

## 四、改进优先级

| 任务 | 优先级 | 难度 | 预计工作量 |
|------|--------|------|-----------|
| 修改 `deck_planner.py` 支持 `<slide>` 标签 | P0 | 中 | 1 天 |
| 移除 `MAX_BODY_CHAPTERS = 3` 硬限制 | P0 | 极小 | 30 分钟 |
| 新增 CLI 参数 `--min-slides` / `--max-slides` | P1 | 小 | 半天 |
| 扩展模板 manifest.json 的 slide_pools | P1 | 小 | 1 小时 |
| 更新 INPUT_SPEC.md 文档 | P1 | 极小 | 1 小时 |

---

## 五、测试计划

### 5.1 功能测试

| 测试用例 | 输入 | 预期输出 |
|---------|------|---------|
| 15 页 HTML | 包含 15 个 `<slide>` 标签 | 生成 15 页正文 PPT |
| 指定 pattern | `<slide data-pattern="process_flow">` | 使用 process_flow 布局 |
| 页数范围 | `--min-slides 10 --max-slides 20` | 在范围内自动调整 |
| 超出模板容量 | 20 个 `<slide>` 但模板只支持 10 页 | 报错提示修改 manifest.json |

### 5.2 回归测试

确保不破坏现有的功能：
- `samples/input/uat_plan_sample.html` 仍然能正常渲染
- `samples/input/architecture_program_sample.html` 仍然能正常渲染
- `ai-make` 命令不受影响

---

## 六、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| HTML 解析逻辑复杂度增加 | 可能引入 bug | 充分单元测试，保留旧路径兼容 |
| 模板容量不足需要手动修改 manifest.json | 用户体验下降 | 提供清晰的错误提示和文档 |
| 用户期望与实现仍存在差距 | 需求变更 | 及时沟通，分阶段落地 |

---

## 七、相关文件清单

```
需要修改的文件：
- tools/sie_autoppt/deck_planner.py         # 核心解析逻辑
- tools/sie_autoppt/config.py              # 移除硬上限
- tools/sie_autoppt/cli.py                # 新增参数
- tools/sie_autoppt/generator.py          # 容量检查
- assets/templates/sie_template.pptx       # 扩展 slide pools（可选）
- assets/templates/sie_template.manifest.json  # 扩展 slide pools

需要新增的文件：
- tests/test_deck_planner_slide_tags.py   # 新增测试用例
- docs/HTML_INPUT_SPEC_V2.md             # 新版 HTML 输入规范

需要更新的文件：
- docs/INPUT_SPEC.md                      # 标注旧版为 deprecated
- docs/README.md                          # 更新使用示例
```

---

## 八、后续优化方向

1. **支持更丰富的 HTML 元素**
   - 图片、表格、图表
   - CSS 样式识别（颜色、字体）

2. **智能 pattern 推断**
   - 根据内容特征自动选择最合适的 pattern
   - 学习用户偏好

3. **模板热更新**
   - 无需重启即可加载新模板
   - 支持用户自定义模板

---

*本方案由产品需求驱动生成，如有疑问请联系产品方确认。*
