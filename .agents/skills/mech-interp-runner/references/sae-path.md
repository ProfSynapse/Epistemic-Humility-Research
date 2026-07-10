# SAE Path

Load this when running SAE feature screens. Use SAE scripts as screens, not
causal evidence.

```bash
python experiments/common/mechinterp/sae_smoke.py \
  --config archive/experiment/phase1/probe/config/selfaware-sae-screens/phase3_selfaware_sae_smoke.yaml
python experiments/common/mechinterp/sae_train.py \
  --config archive/experiment/phase1/probe/config/selfaware-sae-screens/phase3_selfaware_sae_pilot.yaml
python experiments/common/mechinterp/sae_feature_analysis.py \
  --config archive/experiment/phase1/probe/config/selfaware-sae-screens/phase3_selfaware_sae_feature_analysis.yaml
python experiments/common/mechinterp/sae_behavior_feature_analysis.py \
  --config archive/experiment/phase1/probe/config/selfaware-sae-screens/phase3_selfaware_sae_behavior_feature_analysis.yaml
```

Treat outputs as plumbing/training/feature-screening evidence only. Candidate
features need row inspection, geometry, logit controls, and generated-answer
replay before being described as mechanisms.

For SelfAware extraction manifests, if using
`readiness_checks.require_extraction_manifest`, specify `label_counts`
explicitly (`known: 556`, `unknown: 677`). Omitting the field can be interpreted
as an expected empty map and fail before model loading.
