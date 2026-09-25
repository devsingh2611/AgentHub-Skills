# Text Quality Analyzer

Analyze plain text and return concise, deterministic quality signals. Use this skill to review skill instructions, release notes, knowledge content, and similar prose before publication.

## Inputs

- Plain text to analyze.
- Optional context describing the content being reviewed.

## Analysis

Report the following:

- Word count.
- Sentence count.
- Estimated reading time, calculated at 200 words per minute.
- Average sentence length.
- Warnings for empty or overly short content, long sentences, and repeated terminology.

Keep results factual and reproducible. Do not invent stylistic scores or recommendations that are not supported by the supplied text.

## Output

Return a compact report with measured values followed by any applicable warnings. If no warnings apply, state that no quality signals were detected.

## Usage

```python
from skill import analyze_text

report = analyze_text("Provide a clear summary. Include expected outcomes.")
```