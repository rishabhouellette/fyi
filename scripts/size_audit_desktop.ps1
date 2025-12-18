param(
    [string]$Root = 'D:\FYIUploader\desktop',
    [int]$Top = 30
)

$ErrorActionPreference = 'SilentlyContinue'

if (-not (Test-Path -LiteralPath $Root)) {
    Write-Error "Root path not found: $Root"
    exit 1
}

Write-Host "Scanning top-level sizes under: $Root" -ForegroundColor Cyan

Get-ChildItem -LiteralPath $Root -Force | ForEach-Object {
    $item = $_
    $sum = (Get-ChildItem -LiteralPath $item.FullName -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    if (-not $sum) { $sum = 0 }
    [pscustomobject]@{
        Name     = $item.Name
        SizeGB   = [math]::Round(($sum / 1GB), 3)
        FullName = $item.FullName
    }
} | Sort-Object SizeGB -Descending | Select-Object -First $Top | Format-Table -AutoSize
