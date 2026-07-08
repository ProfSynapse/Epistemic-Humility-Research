# jspace-jlens-r1 result provenance

Full-corpus Modal run for `j-space-localization-qwen3-4b`.

- Run tag: `jspace-jlens-r1`
- Modal app: `ap-vnvIl5WaUIDDwhEN2UWwFF`
- Function call: `fc-01KWZ03RBXAK7HQKV7SQ4AM9GX`
- Model: `unsloth/Qwen3-4B`
- Seed: 20260707
- Prompts: 1000, fetched at runtime from private HF staging and never committed
- Profile layers: `2,5,8,11,14,17,20,23,26,29,32,35,36`
- Profile random directions: 5
- Reported runtime: 10760.2 seconds

Files copied from Modal Volume `eh-jspace-jlens-logs/ckpt/jspace-jlens-r1/`:

- `smoke_full.json`
- `h1_full.json`
- `profile_full.json`
- `job_log.txt`
- `DONE`

Containment note: these files contain numeric metrics, token strings from the
model vocabulary, and run metadata. They do not contain prompt/question text,
aliases, full corpus rows, or row keys.

Summary:

- Full-corpus smoke: mean cosine similarity 0.9811, mean top-10 overlap 0.82,
  top-1 match 3/5.
- H1 verbalization: `u_d_L34` is answer/reply-like; `pos_ctrl_L34` and
  `c_hat_L34` are self/absence/error/impossibility-like; `neg_ctrl_L34` is a
  noisy local null.
- Profile: effective-dimensionality fraction peaks at hs=26 (0.01057), with a
  mid-late band across hs=23-29 and a decline by hs=35/36. L34 maps to hs=34,
  placing it just after the peak workspace-like band.
