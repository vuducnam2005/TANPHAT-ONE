param(
    [ValidateSet('setup', 'start', 'stop', 'status', 'test', 'upgrade', 'smoke', 'lock')]
    [string]$Action = 'status',
    [string]$PgBin
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    if ($Action -ne 'setup') { throw 'Run scripts/dev.ps1 setup first.' }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 -m venv (Join-Path $taskRoot '.venv')
    } else {
        & python -m venv (Join-Path $taskRoot '.venv')
    }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}
& $taskPython -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)"
if ($LASTEXITCODE -ne 0) { throw 'This development lock requires Python 3.12. Create .venv with Python 3.12.' }
if ($Action -eq 'setup') {
    $taskRequirements = Join-Path $taskRoot 'ops\requirements-windows-py312.lock.txt'
    if (-not (Test-Path -LiteralPath $taskRequirements)) { $taskRequirements = Join-Path $taskRoot 'requirements.txt' }
    & $taskPython -m pip install -r $taskRequirements
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the Python dependencies.' }
}
$taskArgs = @((Join-Path $PSScriptRoot 'dev.py'), $Action)
if ($PgBin) { $taskArgs += @('--pg-bin', $PgBin) }
& $taskPython @taskArgs
exit $LASTEXITCODE
