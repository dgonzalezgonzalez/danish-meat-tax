param(
    [string]$Python = "python",
    [string]$RawPath = "data/raw/heissepreise_20260609T092146Z.json",
    [switch]$AllowUpdatedInputs,
    [switch]$CompilePaper
)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
$previousPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = Join-Path $projectRoot "src"
    if (-not $AllowUpdatedInputs) {
        & $Python scripts/verify_inputs.py
        if ($LASTEXITCODE -ne 0) { throw "Input verification failed." }
    }
    & $Python main.py process --raw-path $RawPath
    if ($LASTEXITCODE -ne 0) { throw "Processing failed." }
    & $Python main.py panel --frequency monthly
    if ($LASTEXITCODE -ne 0) { throw "Panel construction failed." }
    & $Python main.py estimate
    if ($LASTEXITCODE -ne 0) { throw "Stata estimation failed." }
    & $Python main.py outputs
    if ($LASTEXITCODE -ne 0) { throw "Calibration failed." }
    if ($CompilePaper) {
        Push-Location paper
        try {
            & pdflatex -interaction=nonstopmode -halt-on-error main.tex
            if ($LASTEXITCODE -ne 0) { throw "First TeX pass failed." }
            & bibtex main
            if ($LASTEXITCODE -ne 0) { throw "Bibliography failed." }
            1..2 | ForEach-Object {
                & pdflatex -interaction=nonstopmode -halt-on-error main.tex
                if ($LASTEXITCODE -ne 0) { throw "TeX pass failed." }
            }
        } finally { Pop-Location }
    }
} finally {
    $env:PYTHONPATH = $previousPythonPath
    Pop-Location
}
