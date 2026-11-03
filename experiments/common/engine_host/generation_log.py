"""EHR generation-text contract over the host-owned resumable log."""

from .runlog import RunLog, RunLogError


def open_generation_runlog(path, run_config, *, text_field="out_text", textless_reason=None):
    if textless_reason is not None:
        if not isinstance(textless_reason, str) or not textless_reason.strip():
            raise RunLogError("textless_reason must explain why no text is produced")
        return RunLog(path, {**run_config, "textless_reason": textless_reason})
    return RunLog(path, run_config, required_fields=(text_field,))
