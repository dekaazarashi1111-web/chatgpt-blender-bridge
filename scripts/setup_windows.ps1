$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $RootDir

Get-Command python | Out-Null
Get-Command git | Out-Null
Get-Command gh | Out-Null

if (-not (Test-Path "config.json")) {
    Copy-Item "config.example.json" "config.json"
}

python bridge_cli.py doctor
python bridge_cli.py validate

Write-Output "SETUP=PASS root=$RootDir"
