# Row-Pattern Analysis Artifacts

Generated exploratory locked training-regimen row-pattern artifacts for Paper 2.

- `row_pattern_report.md` summarizes the deterministic row-pattern pass.
- `row_pattern_outputs/` contains row masters, transition tables, schema audit, and validation summary.
- `unknown_question_labels/` contains exploratory semantic-label manifests and category-by-regimen outputs.

Regenerate the row-pattern tables with:

```bash
python archive/experiment/phase1/eval/analysis/row_pattern_analysis.py --write --output-dir papers/paper-2-training-regimen/analysis/row-pattern/row_pattern_outputs
```

Then regenerate downstream unknown-question/category outputs with:

```bash
python archive/experiment/phase1/eval/analysis/unknown_question_labels/build_unknown_question_labels.py --input-dir papers/paper-2-training-regimen/analysis/row-pattern/row_pattern_outputs --output-dir papers/paper-2-training-regimen/analysis/row-pattern/unknown_question_labels
python archive/experiment/phase1/eval/analysis/unknown_question_labels/category_regimen_analysis.py --labels papers/paper-2-training-regimen/analysis/row-pattern/unknown_question_labels/llm_labeled_unknown_answered_questions_v3.csv --row-dir papers/paper-2-training-regimen/analysis/row-pattern/row_pattern_outputs --output-dir papers/paper-2-training-regimen/analysis/row-pattern/unknown_question_labels
```
