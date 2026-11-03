# Derived desktop runtime

Use the owner's selected T7 E: drive for build artifacts and run outputs.
Keep source data and credentials out of the image context. This directory is
a host-owned image recipe, not an engine backend or a qualification claim.

1. Inspect the live Docker Desktop daemon and the selected base image's full ID.
   A tag in native WSL's separate store is not the same image.
2. Build reviewed engine and EHR host wheels. Record their source commits and
   SHA256s. Acquire only the base dependencies missing or incompatible in the
   chosen image, as pinned compatible wheels. Do not replace Torch or the model
   stack to resolve a host-only dependency.
3. Create a private build context with this Dockerfile and a `wheels/` directory
   containing those exact wheels. Verify all wheel SHA256s against the build
   manifest before building. `--no-deps` prevents a resolver from changing the
   existing GPU runtime; `pip check` must pass.
4. Build with `--build-arg BASE_IMAGE=sha256:<actual-id>` and record the resulting
   image ID. Run `ehr-engine doctor`, project validation, CUDA visibility and the
   registered bounded model/intervention smoke inside it.
5. Pin the derived image digest in the new experiment only after review.

Historical runtime images remain unchanged. The base runner entrypoint prints
its original provenance. Record the derived ID and actual installed engine and
host identities alongside it rather than treating the base's baked-in source
revision as the engine installed by this layer.
