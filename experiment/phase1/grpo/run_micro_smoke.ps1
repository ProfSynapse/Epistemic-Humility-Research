param(
    [ValidateSet("base", "base-pilot", "sft-seed1")]
    [string]$Mode = "base",
    [int]$MaxUsedMemoryMiB = 4096,
    [switch]$DebugReward,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
Set-Location $repoRoot

$config = switch ($Mode) {
    "base" { "experiment/phase1/grpo/configs/grpo_base_micro_smoke.yaml" }
    "base-pilot" { "experiment/phase1/grpo/configs/grpo_base_pilot.yaml" }
    "sft-seed1" { "experiment/phase1/grpo/configs/grpo_sft_seed1_micro_smoke.yaml" }
}

$requiredData = switch ($Mode) {
    "base-pilot" { "scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train.jsonl" }
    default { "scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train_smoke_32.jsonl" }
}
if (-not (Test-Path -LiteralPath $requiredData)) {
    throw "Missing GRPO dataset: $requiredData. Run build_grpo_dataset.py and make_smoke_subset.py first."
}

$usedMemory = $null
try {
    $raw = & nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
    $usedMemory = [int]($raw | Select-Object -First 1)
} catch {
    Write-Warning "Could not read GPU memory with nvidia-smi: $_"
}

if ($null -ne $usedMemory -and -not $Force -and $usedMemory -gt $MaxUsedMemoryMiB) {
    throw "GPU already using ${usedMemory}MiB, above ${MaxUsedMemoryMiB}MiB. Re-run with -Force to override."
}

$debugArgs = @()
if ($DebugReward) {
    $debugPath = "scratch/grpo_bootstrap/reward_debug/${Mode}_latest.jsonl"
    $debugArgs = @("-e", "GRPO_REWARD_DEBUG_PATH=/workspace/repo/$debugPath")
    if (Test-Path -LiteralPath $debugPath) {
        Remove-Item -LiteralPath $debugPath
    }
    Write-Host "Reward debug trace: $debugPath"
}

docker run --rm --gpus all --ipc=host --entrypoint python3 `
    -e HF_HOME=/workspace/repo/.cache/hf `
    -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub `
    @debugArgs `
    -v "${repoRoot}:/workspace/repo" `
    -w /workspace/repo `
    unsloth/unsloth:latest `
    synaptic-tuner/Trainers/grpo/train_grpo.py `
    --config $config
