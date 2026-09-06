# Submit-side container for the Modal smoke of the prepared path.
#
# Design of record: docs/architecture/prepared-path-alpine-diagnostic.md 29.10.
#
# This container SUBMITS. It never trains. It carries no GPU stack, no CUDA, no
# trainer image and no ML dependencies. The training container is a different
# thing entirely, built by the provider from a digest-pinned reference and given
# its credentials by a named Modal Secret.
#
# What deliberately stays OUT of this image, each for a stated reason:
#   * Project and engine source. The deployment attaches sources with copy
#     disabled and the training container materializes source by cloning at run
#     time, so baking a source layer here would create a second, divergent copy.
#     Source is bind-mounted read-only at run time instead.
#   * Credentials of every kind. They reach the SDK at run time as in-process
#     parameters and a closed child environment block, never as a layer, never
#     as argv, never as any durable artifact.
#   * A container-side interpreter pin. The engine's runtime lock pins CPython
#     3.11.14 at /opt/conda/bin/python3 for the TRAINING container. That pin is
#     container-side and does not cross the seam, so it does not constrain this
#     image. This base resolves to CPython 3.11.16 on x86_64, which matches the
#     cp311 x86_64 wheels the launcher closure was built for.
#
# Base pinned by digest, resolved 2026-09-06 from python:3.11-slim-bookworm.
FROM python@sha256:528257d48c1da0dcecc2e725d1ae34498d60c965f1241e39cd6a85a8859bdf84

# An explicit, short PATH. The operator PATH is NOT inherited: it was measured
# at 5248 bytes in the WSL shell and 3903 on Windows, and launcher.py:628
# refuses any allowlisted child environment value over 4096 bytes through
# _validated_child_environment_value at launcher.py:104-113. Gate G2 measures
# the byte length of the PATH below from inside the built container.
ENV PATH=/usr/local/bin:/usr/bin:/bin \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONNOUSERSITE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Exactly the hash-locked launcher closure, installed with no resolution.
# deployment_v1.py:95 and facade.py:71-74 compare the SDK version for EQUALITY,
# so 1.5.4 is the only acceptable outcome and the build fails closed otherwise.
# The flags match launcher.py:401-402. --no-deps is what makes "must not
# resolve" literal: the lock is a complete closure of 37 hash-pinned lines.
COPY modal-launcher-v1.lock /tmp/modal-launcher-v1.lock
RUN python3 -m pip install \
        --require-hashes --only-binary :all: --no-deps \
        --requirement /tmp/modal-launcher-v1.lock \
 && rm -f /tmp/modal-launcher-v1.lock \
 && python3 -c "import modal; assert modal.__version__ == '1.5.4', modal.__version__"

# Least privilege: the submit process is not root.
#
# The user is a bare numeric id with NO passwd entry. That is deliberate and it
# is also forced: this pinned base carries no `useradd` (it is absent from the
# slim image, and the build fails with exit 127 if you reach for it), and
# installing a package to get one would add a layer for nothing. A numeric
# USER needs no passwd entry to run, so the only real consequence is that the
# process has no home directory of its own. HOME is therefore set to a path
# that exists and is writable, because a library that expands "~" against an
# unset HOME resolves it to "/" and then fails on a write it should never have
# attempted. Nothing here needs a home: credentials reach the SDK in-process,
# not from a config file under a home directory.
RUN install -d -o 1000 -g 1000 -m 0755 /workspace
ENV HOME=/tmp
USER 1000:1000
WORKDIR /workspace

# Empty entrypoint so the workload argv is never discarded. B-4 on the local
# lane was exactly this defect: the image ENTRYPOINT swallowed the argv.
ENTRYPOINT []
CMD ["python3", "-c", "import modal; print(modal.__version__)"]
