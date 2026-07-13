# SelfAware Hidden-State Extraction Configs

Historical mechinterp SelfAware hidden-state extraction manifests migrated from
`experiment/phase1/probe/config/`.

These configs prepared or launched frozen-manifest SelfAware extraction runs for
SFT, SFT->DPO, SFT->KTO, clean-SFT, GRPO v2, GRPO-DPO, DPO-GRPO, KTO, and
KTO-GRPO surfaces. They are retained for provenance and as historical templates,
but they are not the live default hidden-state runner entrypoint.

Use `experiment/phase1/probe/config/hidden_state_probe.yaml` for the current
generic smoke/default path. New evidence-producing extraction cells should live
under `experiments/<slug>/` with pinned instrument configs.
