---
name: academic-research-skills
description: >
  学术科研综合技能包。整合 34 个核心科研技能，来源：K-Dense-AI (7800+ stars) + ChineseResearchLaTeX (746 stars)。
  覆盖：科学写作、数据可视化、文献检索、假设生成、同行评审、引用管理、科研海报、演示制作、
  生物信息学、化学信息学、科学数据库、NSFC标书写作、中文系统综述。
  触发词：科研、学术、文献、图表、可视化、数据分析、LaTeX、实验设计、统计分析、
  生物信息、化学信息、PubMed、UniProt、NSFC、国自然、标书、立项依据、研究内容、系统综述。
  NOT for：完整论文撰写（用paper-composer）/论文降重润色（用ai-deweight）/
  文献搜索下载（用library-researcher）/非学术的数据分析或编程/
  普通代码开发（即使涉及"数据分析"关键词，如果不是学术科研场景也不要触发）/
  UI设计或前端开发中的"图表"（用ui-ux-pro-max）。
  本技能是科研工具箱，不是论文写作流程，也不是通用编程工具。
context: fork
agent: Explore
---

# Academic Research Skills

学术科研综合技能包，整合两大高星仓库的核心科研技能。

**来源**:
- `k-dense-ai/claude-scientific-skills` (7,805 stars) - 英文科研工具
- `huangwb8/chineseresearchlatex` (746 stars) - 中文科研 LaTeX

## 子技能路由表

当用户请求匹配以下触发词时，**必须读取对应的子技能 SKILL.md 文件并按其指令执行**。

### 中文科研 (ChineseResearchLaTeX)

| 类别 | 子技能 | 触发词 | 路径 |
|------|--------|--------|------|
| **NSFC** | nsfc-justification-writer | 立项依据、NSFC立项、国自然立项 | `sub-skills/nsfc-justification-writer/SKILL.md` |
| **NSFC** | nsfc-research-content-writer | 研究内容、研究目标、技术路线、创新点 | `sub-skills/nsfc-research-content-writer/SKILL.md` |
| **NSFC** | nsfc-research-foundation-writer | 研究基础、前期工作、可行性分析 | `sub-skills/nsfc-research-foundation-writer/SKILL.md` |
| **NSFC** | nsfc-abstract | NSFC摘要、标书摘要、中英文摘要 | `sub-skills/nsfc-abstract/SKILL.md` |
| **NSFC** | nsfc-bib-manager | NSFC引用、标书参考文献、bib管理 | `sub-skills/nsfc-bib-manager/SKILL.md` |
| **综述** | systematic-literature-review | 系统综述、文献综述、related work、文献调研 | `sub-skills/systematic-literature-review/SKILL.md` |
| **综述** | get-review-theme | 提取综述主题、综述选题 | `sub-skills/get-review-theme/SKILL.md` |
| **综述** | check-review-alignment | 核查综述引用、引用校验 | `sub-skills/check-review-alignment/SKILL.md` |
| **LaTeX** | make_latex_model | LaTeX模板优化、模板对齐 | `sub-skills/make_latex_model/SKILL.md` |
| **LaTeX** | complete_example | LaTeX示例生成、填充示例 | `sub-skills/complete_example/SKILL.md` |
| **LaTeX** | transfer_old_latex_to_new | LaTeX模板迁移、标书迁移 | `sub-skills/transfer_old_latex_to_new/SKILL.md` |
| **工具** | guide-updater | 更新项目指南、沉淀洞见 | `sub-skills/guide-updater/SKILL.md` |

### 英文科研 (K-Dense-AI)

| 类别 | 子技能 | 触发词 | 路径 |
|------|--------|--------|------|
| **写作** | scientific-writing | 论文写作、科学写作、学术写作、IMRAD | `sub-skills/scientific-writing/SKILL.md` |
| **写作** | literature-review | 文献综述、综述写作、review | `sub-skills/literature-review/SKILL.md` |
| **检索** | research-lookup | 文献检索、查文献、搜索论文、查资料 | `sub-skills/research-lookup/SKILL.md` |
| **检索** | citation-management | 引用、参考文献、BibTeX、引文 | `sub-skills/citation-management/SKILL.md` |
| **分析** | hypothesis-generation | 假设、实验设计、研究问题 | `sub-skills/hypothesis-generation/SKILL.md` |
| **分析** | peer-review | 审稿、评审、论文评价、批判性分析 | `sub-skills/peer-review/SKILL.md` |
| **分析** | exploratory-data-analysis | EDA、探索性分析、数据探索 | `sub-skills/exploratory-data-analysis/SKILL.md` |
| **分析** | statistical-analysis | 统计分析、假设检验、回归分析 | `sub-skills/statistical-analysis/SKILL.md` |
| **可视化** | scientific-visualization | 科研图表、数据可视化、figure | `sub-skills/scientific-visualization/SKILL.md` |
| **可视化** | scientific-schematics | 示意图、流程图、CONSORT、神经网络图 | `sub-skills/scientific-schematics/SKILL.md` |
| **可视化** | matplotlib | matplotlib、pyplot、图表绑定 | `sub-skills/matplotlib/SKILL.md` |
| **可视化** | seaborn | seaborn、统计图表、热力图 | `sub-skills/seaborn/SKILL.md` |
| **可视化** | plotly | plotly、交互图表、动态可视化 | `sub-skills/plotly/SKILL.md` |
| **演示** | scientific-slides | 幻灯片、PPT、演示、slides | `sub-skills/scientific-slides/SKILL.md` |
| **演示** | latex-posters | 海报、poster、会议海报、LaTeX海报 | `sub-skills/latex-posters/SKILL.md` |
| **机器学习** | scikit-learn | sklearn、机器学习、分类、聚类 | `sub-skills/scikit-learn/SKILL.md` |
| **数据库** | pubmed-database | PubMed、医学文献、NCBI | `sub-skills/pubmed-database/SKILL.md` |
| **数据库** | openalex-database | OpenAlex、学术搜索、开放获取 | `sub-skills/openalex-database/SKILL.md` |
| **数据库** | uniprot-database | UniProt、蛋白质数据库、序列 | `sub-skills/uniprot-database/SKILL.md` |
| **生信** | biopython | Biopython、序列分析、BLAST | `sub-skills/biopython/SKILL.md` |
| **生信** | scanpy | scanpy、单细胞、scRNA-seq | `sub-skills/scanpy/SKILL.md` |
| **化信** | rdkit | RDKit、分子、化学结构、SMILES | `sub-skills/rdkit/SKILL.md` |

## 执行流程

```
用户请求 → 匹配触发词 → 读取子技能 SKILL.md → 按指令执行
```

**关键步骤**:
1. 识别用户请求中的关键词
2. 从路由表匹配对应子技能
3. **使用 Read 工具读取 `sub-skills/<skill-name>/SKILL.md`**
4. 按子技能的指令和工作流执行任务

## 示例

**用户**: "帮我写 NSFC 立项依据"
**执行**:
1. 匹配 "立项依据" → `nsfc-justification-writer`
2. 读取 `sub-skills/nsfc-justification-writer/SKILL.md`
3. 按其工作流执行

**用户**: "做一个系统综述"
**执行**:
1. 匹配 "系统综述" → `systematic-literature-review`
2. 读取 `sub-skills/systematic-literature-review/SKILL.md`
3. 按其多阶段流程执行

## 技能来源

- K-Dense-AI: https://github.com/k-dense-ai/claude-scientific-skills
- ChineseResearchLaTeX: https://github.com/huangwb8/chineseresearchlatex
