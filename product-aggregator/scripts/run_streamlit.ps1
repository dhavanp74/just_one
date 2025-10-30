<#
Run the Streamlit app for this repository.

Usage:
  # from PowerShell
  cd path\to\product-aggregator
  .\scripts\run_streamlit.ps1

This script prefers the project's venv at .\.venv. If not found, it prints
conda instructions to run the app.
#>

param()

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition | Split-Path -Parent
Push-Location $RepoRoot

$venvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "Found venv python at: $venvPython" -ForegroundColor Green
    Write-Host "Running Streamlit with venv python..." -ForegroundColor Cyan
    # Use the venv python directly to avoid activation/ExecutionPolicy issues
    & $venvPython -m pip install --upgrade pip | Out-Null
    & $venvPython -m streamlit run ui\app.py
    Pop-Location
    exit 0
}

Write-Host "No .venv found in the project. If you prefer conda, run the following in Anaconda Prompt:" -ForegroundColor Yellow
Write-Host "conda create -n product-agg python=3.11 -y" -ForegroundColor Gray
Write-Host "conda activate product-agg" -ForegroundColor Gray
Write-Host "conda install -c conda-forge pyarrow -y" -ForegroundColor Gray
Write-Host "python -m pip install --upgrade pip" -ForegroundColor Gray
Write-Host "python -m pip install requests beautifulsoup4 lxml undetected-chromedriver selenium streamlit pandas" -ForegroundColor Gray
Write-Host "python -m streamlit run product-aggregator\ui\app.py" -ForegroundColor Gray

Pop-Location
exit 1
