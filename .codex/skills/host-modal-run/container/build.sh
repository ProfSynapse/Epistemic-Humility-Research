#!/usr/bin/env bash
# Build the submit-side container of the Modal smoke, and optionally run G2 in it.
#
# Design of record: docs/architecture/prepared-path-alpine-diagnostic.md 29.10,
# gate G2 in 29.12.
#
# Why this script exists rather than a bare `docker build`
# --------------------------------------------------------
# Three things about this build are easy to get wrong by hand, and each of them
# fails in a way that looks like something else:
#
#   1. THE BUILD CONTEXT IS NOT THIS DIRECTORY. The Dockerfile copies exactly
#      one file, `modal-launcher-v1.lock`, and that file lives in the engine
#      submodule at `synaptic-tuner/requirements/`, which holds nothing else.
#      Using the engine's requirements directory as the context is therefore
#      both minimal and exact: the daemon receives one file. Running the build
#      from the Dockerfile's own directory would send the wrong context and the
#      COPY would fail with a message about a missing file, not about a wrong
#      context.
#
#   2. DOCKER DESKTOP IS A WINDOWS PROCESS. Called from WSL, `docker.exe` reads
#      every path as a Windows path. A POSIX build context or a POSIX -v source
#      is not resolved, it is misresolved. `wslpath -w` does the translation.
#
#   3. THE ENDPOINT IS CONSTRUCTED, NOT LOOKED UP. B-13 (section 22) recorded
#      that `docker context inspect` needs USERPROFILE to resolve the .docker
#      config directory, and fails opaquely without it. The remedy adopted
#      there, and reused here, is to name the named-pipe endpoint explicitly
#      with --host so no context lookup happens at all.
#
# The image carries the SDK and nothing else: no engine source, no project
# source, no trainer image or ML stack, and no credential of any kind. The
# engine arrives at run time as a read-only bind mount, and credentials arrive
# in-process at submit time.
#
# Usage
# -----
#   ./build.sh                 # build the image
#   ./build.sh --g2            # build, then run gate G2 inside it
#   ./build.sh --g2 --no-build # run G2 against the image already built
#
# Environment overrides: SUBMIT_IMAGE_TAG, DOCKER_BIN, DOCKER_HOST_ENDPOINT.

set -euo pipefail

IMAGE_TAG="${SUBMIT_IMAGE_TAG:-synaptic-modal-submit:v1}"
ENDPOINT="${DOCKER_HOST_ENDPOINT:-npipe:////./pipe/dockerDesktopLinuxEngine}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${HERE}/../../.." && pwd)"
ENGINE_ROOT="${REPO_ROOT}/synaptic-tuner"
BUILD_CONTEXT="${ENGINE_ROOT}/requirements"
DOCKERFILE="${HERE}/Dockerfile"

RUN_G2=0
DO_BUILD=1
for argument in "$@"; do
  case "${argument}" in
    --g2) RUN_G2=1 ;;
    --no-build) DO_BUILD=0 ;;
    -h|--help) sed -n '1,40p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown argument: ${argument}" >&2; exit 2 ;;
  esac
done

# --- platform: which docker, and does it need Windows paths ----------------
if [[ -n "${DOCKER_BIN:-}" ]]; then
  DOCKER="${DOCKER_BIN}"
elif command -v docker.exe >/dev/null 2>&1; then
  DOCKER="docker.exe"
else
  DOCKER="docker"
fi

# `docker.exe` is a Windows binary: it needs Windows paths and the explicit
# named-pipe endpoint. A native docker needs neither.
NEEDS_WINDOWS_PATHS=0
HOST_ARGS=()
if [[ "${DOCKER}" == *.exe ]]; then
  NEEDS_WINDOWS_PATHS=1
  HOST_ARGS=(--host "${ENDPOINT}")
fi

to_daemon_path() {
  if [[ "${NEEDS_WINDOWS_PATHS}" -eq 1 ]]; then
    wslpath -w "$1"
  else
    printf '%s' "$1"
  fi
}

# --- preconditions ---------------------------------------------------------
if [[ ! -f "${BUILD_CONTEXT}/modal-launcher-v1.lock" ]]; then
  echo "FAIL the hash-locked requirements file is missing:" >&2
  echo "     ${BUILD_CONTEXT}/modal-launcher-v1.lock" >&2
  echo "     the engine submodule is probably not checked out" >&2
  exit 2
fi

context_entries="$(find "${BUILD_CONTEXT}" -mindepth 1 -maxdepth 1 | wc -l)"
echo "docker binary : ${DOCKER}"
if [[ "${#HOST_ARGS[@]}" -gt 0 ]]; then
  echo "endpoint      : ${ENDPOINT}  (constructed, no context lookup)"
fi
echo "dockerfile    : ${DOCKERFILE}"
echo "build context : ${BUILD_CONTEXT}  (${context_entries} entry/entries)"
echo "image tag     : ${IMAGE_TAG}"
echo

# --- build -----------------------------------------------------------------
if [[ "${DO_BUILD}" -eq 1 ]]; then
  # A parse-and-validate pass first. It costs no layer and it separates a
  # malformed recipe from a failing install, which otherwise both surface as a
  # build failure partway through.
  echo "== docker build --check =="
  "${DOCKER}" "${HOST_ARGS[@]}" build --check \
    -f "$(to_daemon_path "${DOCKERFILE}")" \
    "$(to_daemon_path "${BUILD_CONTEXT}")"

  echo
  echo "== docker build =="
  "${DOCKER}" "${HOST_ARGS[@]}" build \
    -t "${IMAGE_TAG}" \
    -f "$(to_daemon_path "${DOCKERFILE}")" \
    "$(to_daemon_path "${BUILD_CONTEXT}")"
  echo
fi

# --- G2 --------------------------------------------------------------------
if [[ "${RUN_G2}" -eq 1 ]]; then
  # The gitlink is measured on the HOST, where git lives: the container carries
  # no git and no engine history. Containment (inside the container) proves
  # which tree was imported; the gitlink proves which commit that tree is at.
  # Neither implies the other, so G2 takes both and checks them separately.
  if [[ -x "/mnt/c/Program Files/Git/cmd/git.exe" ]] && [[ "${REPO_ROOT}" == /mnt/* ]]; then
    GIT="/mnt/c/Program Files/Git/cmd/git.exe"
  else
    GIT="git"
  fi
  # A Windows git.exe rejects a POSIX path passed to -C with a fatal exit 128,
  # so every call below sets the working directory instead of using -C.
  GITLINK_EXPECTED="$(cd "${REPO_ROOT}" && "${GIT}" -c safe.directory='*' \
      ls-tree HEAD -- synaptic-tuner | awk '{print $3}')"
  GITLINK_OBSERVED="$(cd "${ENGINE_ROOT}" && "${GIT}" -c safe.directory='*' \
      rev-parse HEAD)"
  OPERATOR_PATH_BYTES="${#PATH}"

  SCRIPTS_DIR="${HERE}/../scripts"

  echo "== gate G2 (inside the submit container) =="
  echo "gitlink expected : ${GITLINK_EXPECTED}"
  echo "gitlink observed : ${GITLINK_OBSERVED}"
  echo "operator PATH    : ${OPERATOR_PATH_BYTES} bytes"
  echo

  # No network policy is asserted on this run. The gate itself needs no
  # network, but the submit invocation the container exists for does, and this
  # lane's egress is unrestricted at this pin. Nothing here should be read as a
  # network property of the submit container.
  "${DOCKER}" "${HOST_ARGS[@]}" run --rm \
    -v "$(to_daemon_path "${ENGINE_ROOT}")":/engine:ro \
    -v "$(to_daemon_path "${SCRIPTS_DIR}")":/gates:ro \
    -w /workspace \
    "${IMAGE_TAG}" \
    python3 /gates/g2_submit_container.py \
      --engine-root /engine \
      --gitlink-expected "${GITLINK_EXPECTED}" \
      --gitlink-observed "${GITLINK_OBSERVED}" \
      --operator-path-bytes "${OPERATOR_PATH_BYTES}"
fi
