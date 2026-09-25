# Text Quality Analyzer Skill

Analyzes plain text for concise, deterministic quality signals. It is useful
for reviewing skill instructions, release notes, and knowledge content before
publication.

## Behavior

- Counts words and sentences.
- Estimates reading time at 200 words per minute.
- Reports average sentence length.
- Warns about empty or overly short content, long sentences, and repeated
	terminology.

## Usage

```python
from skill import analyze_text

report = analyze_text("Provide a clear summary. Include expected outcomes.")
```