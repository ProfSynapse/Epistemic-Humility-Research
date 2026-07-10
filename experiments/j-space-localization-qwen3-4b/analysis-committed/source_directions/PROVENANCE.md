# j-space-localization-qwen3-4b source directions provenance

The four direction JSONs in this directory are committed because they are this
project's derived artifacts, not dataset text.

As of the Modal launch-prep update, all four H1 direction inputs were copied
from the sibling `two-signal-caution-regulation-instruct` worktree at commit
`8f277410` and were fit on the same bf16 substrate used by this J-lens run:
`unsloth/Qwen3-4B`.

Files:

- `u_d_L34.json` from `experiments/two-signal-caution-regulation-instruct/analysis-committed/u_d_L34.json`
- `pos_ctrl_L34.json` from `experiments/two-signal-caution-regulation-instruct/analysis-committed/source_directions/pos_ctrl_L34.json`
- `neg_ctrl_L34.json` from `experiments/two-signal-caution-regulation-instruct/analysis-committed/source_directions/neg_ctrl_L34.json`
- `c_hat_L34.json` from `experiments/two-signal-caution-regulation-instruct/analysis-committed/c_hat_L34.json`

Each JSON file carries its own machine-readable `provenance` block with the fit
method, substrate, base model, layer label, and source-pool hashes. The previous
J-space prep state used older copied direction artifacts from bnb/4-bit-derived
fits; local H1 smoke notes based on those inputs remain notebook orientation
only. The full-corpus Modal run uses the bf16 files in this directory.
