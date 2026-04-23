Param(
    [string]$PythonCommand = "python"
)

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    & $PythonCommand -m venv .venv
}

Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

Write-Host "Installing requirements..."
pip install -r requirements.txt

Write-Host "Setup complete."
Write-Host "Next: copy .env.example to .env and set GROQ_API_KEY"
