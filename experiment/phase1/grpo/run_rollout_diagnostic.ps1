param(
    [ValidateSet("base", "sft-seed1")]
    [string]$Mode = "base",
    [int]$MaxRows = 4,
    [int]$NumRollouts = 4,
    [int]$MaxCompletionLength = 256,
    [double]$Temperature = 1.0,
    [double]$TopP = 0.95,
    [int]$MaxUsedMemoryMiB = 4096,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
Set-Location $repoRoot

$config = switch ($Mode) {
    "base" { "experiment/phase1/grpo/configs/grpo_base_micro_smoke.yaml" }
    "sft-seed1" { "experiment/phase1/grpo/configs/grpo_sft_seed1_micro_smoke.yaml" }
}

$smokeData = "scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train_smoke_32.jsonl"
if (-not (Test-Path -LiteralPath $smokeData)) {
    throw "Missing smoke dataset: $smokeData. Run build_grpo_dataset.py and make_smoke_subset.py first."
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

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputDir = "scratch/grpo_bootstrap/diagnostics/${Mode}_${timestamp}"

docker run --rm --gpus all --ipc=host --entrypoint python3 `
    -e HF_HOME=/workspace/repo/.cache/hf `
    -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub `
    -v "${repoRoot}:/workspace/repo" `
    -w /workspace/repo `
    unsloth/unsloth:latest `
    experiment/phase1/grpo/rollout_reward_diagnostic.py `
    --config $config `
    --output-dir $outputDir `
    --max-rows $MaxRows `
    --num-rollouts $NumRollouts `
    --max-completion-length $MaxCompletionLength `
    --temperature $Temperature `
    --top-p $TopP
