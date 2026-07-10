"""Layer constants for j-space-midband-write-sweep-qwen3-4b."""

HS_INDICES = [23, 26, 29, 34]
LATE_REFERENCE_HS = 34


def hs_to_block(hs_index: int) -> int:
    """HF hidden_states index -> 0-indexed decoder block for direction JSON."""
    if hs_index < 1:
        raise ValueError(f"hidden_states index must be >=1, got {hs_index}")
    return hs_index - 1


def layer_dir_name(hs_index: int) -> str:
    return f"hs{hs_index}"
