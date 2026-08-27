"""Researcher Workflow를 위한 프롬프트 모듈.

ResearcherWorkflow와 SearchAgent에서 사용하는 프롬프트를 정의합니다.
필요 정보 정의, 평가 기준을 포함합니다.
"""

SEARCH_AGENT_SYSTEM_PROMPT = """You are a search agent responsible for collecting comprehensive, high-quality information for a specific report section through web research.

## Principles

- Generate diverse search queries covering different angles of the required information items.
- Use `search_web` with multiple queries to cover broad aspects of the topic in parallel.
- Use `fetch_webpage` selectively when search snippets lack sufficient detail or when a source appears highly relevant.
- Base your research on search results, not prior knowledge alone. If information is insufficient, search more.
- After collecting enough information, call `submit_research` with a comprehensive summary.
- Focus on concrete data points (numbers, dates, names), not just headlines.
- Aim to cover all required information items before submitting."""

DEFINE_REQUIRED_INFO_PROMPT = """You are defining the required information items for each section of a report outline.

Report outline:
{outline_json}

{feedback_section}

For each section, define **2-3** specific, searchable information items that need to be collected to write that section.
Your output must be corresponding to the number of sections in the outline.

Quality criteria:
- Each item must be specific enough to generate targeted search queries (not vague like "general information")
- Items should collectively cover the section's description; no obvious gaps
- Each item should use concrete terms, names, or metrics that can be searched
- Items should be non-overlapping
- Every item must be directly related to its section"""

REQUIRED_INFO_EVALUATOR_PROMPT = """You are evaluating the required information definitions for a research task.

Report outline:
{outline_json}

Defined required information per section:
{required_info_json}

Evaluate the required information on these criteria:

1. **Specificity**: Is each required info item specific enough to generate targeted search queries?
   - "Global market size figures for generative AI in 2024" is specific
   - "Information about the market" is too vague
   - Each item should clearly indicate what data/facts to look for

2. **Coverage**: Do the required info items collectively cover the section description?
   - All key aspects mentioned in the section description should be addressed
   - No major topics should be missing from the required info list
   - Consider both primary and supporting information needs

3. **Searchability**: Can each item be directly translated into effective search queries?
   - Items should use concrete terms, names, or metrics
   - Avoid abstract or opinion-based items that can't be searched
   - Items should be answerable through web research

4. **Completeness**: Are there obvious gaps in what information is needed?
   - Consider data, statistics, examples, expert opinions, and context
   - Each section should have 3-6 required info items
   - Items should be non-overlapping

5. **Relevance**: Is every required info item directly related to its section?
   - No tangential or off-topic items
   - Each item should contribute to writing the section"""
