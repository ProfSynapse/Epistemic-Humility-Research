# Original hs20 P-struct capture promotion

This is a hash-only descriptor for the first Astra experiment's original-base
capture and its source provenance. It supports reuse by the broader successor.
It contains no questions, generated answers or tensor values.

Private bytes live on T7 at
`E:/SynapticResearch/shared/astra-r1-capture-v1`. Execution snapshots mount this
bundle read-only at `analysis/private_bundle` beside this file. That directory
is ignored. Do not copy its contents into public Git.

`origin.json` pins all 308 files, the historical source identity, original
request/roster/journal lineage, exact raw input files and the original twenty-row
qualification roster. It declares NumPy 2.2.6 for deterministic roster reuse.
Its SHA256 is ab3ff74637e15635ef62d9ae611c20127be3c2d4bf8b124ca67eccc44c960ec6.
Both experiment manifests reference this descriptor. Promotion does not rewrite
the original experiment or relabel its capture as a new extraction.

The separate `decoys-origin.json` describes the original held-back calibration
file. Its private copy is E:/SynapticResearch/shared/astra-r1-decoys-v1/decoys.json.
Mount it read-only at analysis/decoys/decoys.json. It contains 25 examples per
class, keeps its exact original hash, and is separate from the capture bundle.
