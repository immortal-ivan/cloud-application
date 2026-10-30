# Создаёт самоподписанный сертификат для HTTPS (только для учебной разработки).
# Использует openssl из Git for Windows или из PATH.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

$candidates = @(
    (Get-Command openssl -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
    'C:\Program Files\Git\usr\bin\openssl.exe',
    'C:\Program Files\Git\mingw64\bin\openssl.exe'
) | Where-Object { $_ -and (Test-Path $_) }

if (-not $candidates) {
    Write-Host 'openssl не найден. Установите Git for Windows (он содержит openssl) или запустите приложение без HTTPS: HTTPS_ENABLED=false в .env' -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Force certs | Out-Null
& $candidates[0] req -x509 -newkey rsa:2048 -nodes -days 365 `
    -keyout certs/localhost-key.pem -out certs/localhost.pem `
    -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

if ($LASTEXITCODE -ne 0) { Write-Host 'Не удалось создать сертификат' -ForegroundColor Red; exit 1 }
Write-Host 'Готово: certs/localhost.pem и certs/localhost-key.pem' -ForegroundColor Green
