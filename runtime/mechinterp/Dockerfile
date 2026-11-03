# Host-owned derived runtime. BASE_IMAGE must be a local tag
# verified against its recorded full ID, or a registry digest. The build
# context contains reviewed wheels only. BuildKit does not accept a bare image ID.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
COPY wheels/ /opt/ehr-wheels/
RUN python -m pip install --no-cache-dir --no-deps /opt/ehr-wheels/*.whl \
    && python -m pip check
ENV PYTHONUNBUFFERED=1
# Preserve the base runner's provenance entrypoint. Engine/host wheel identity
# is recorded independently by ehr-engine doctor in the launch record.
