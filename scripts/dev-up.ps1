#Requires -Version 5.1
<#
.SYNOPSIS
  Raise the local Docker stand (db + api) and wait until /api/health is ok.
  Does not print passwords, DSN, or cookie values.
#>
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Get-DotEnvValue {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Key
    )
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        $trim = $line.Trim()
        if ($trim -eq "" -or $trim.StartsWith("#")) { continue }
        $eq = $trim.IndexOf("=")
        if ($eq -lt 1) { continue }
        $name = $trim.Substring(0, $eq).Trim()
        if ($name -ne $Key) { continue }
        $raw = $trim.Substring($eq + 1).Trim()
        if ($raw.Length -ge 2) {
            $q = $raw[0]
            if (($q -eq [char]34 -or $q -eq [char]39) -and $raw[-1] -eq $q) {
                $raw = $raw.Substring(1, $raw.Length - 2)
            }
        }
        return $raw
    }
    return $null
}

Write-Host "ndt-tender-scout dev-up (repo root)"

try {
    docker info | Out-Null
} catch {
    Write-Error "Docker is not available. Install/start Docker Desktop, then re-run .\scripts\dev-up.ps1"
    exit 1
}

$envFile = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $envFile -PathType Leaf)) {
    Write-Error ".env is missing. Copy .env.example to .env and set POSTGRES_PASSWORD (do not put the value in chat or git)."
    exit 1
}

$pgPassword = Get-DotEnvValue -Path $envFile -Key "POSTGRES_PASSWORD"
if ([string]::IsNullOrWhiteSpace($pgPassword)) {
    Write-Error "POSTGRES_PASSWORD is empty in .env. Fill it (and Scout account vars). Do not invent or print the password."
    exit 1
}

$cookies = Join-Path $RepoRoot "cookies.rostender.txt"
if (Test-Path -LiteralPath $cookies -PathType Container) {
    Write-Error "cookies.rostender.txt is a directory. Delete it and re-run; Docker on Windows needs a file bind."
    exit 1
}
if (-not (Test-Path -LiteralPath $cookies)) {
    New-Item -ItemType File -Path $cookies | Out-Null
    Write-Host "created empty cookies.rostender.txt (file bind)"
}

Write-Host "docker compose up -d --build"
docker compose up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Error "docker compose up failed (exit $LASTEXITCODE)"
    exit 1
}

function Wait-ServiceHealthy {
    param(
        [Parameter(Mandatory = $true)][string]$Service,
        [int]$TimeoutSec = 180
    )
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $TimeoutSec) {
        $raw = docker compose ps $Service --format json 2>$null
        if ($LASTEXITCODE -eq 0 -and $raw) {
            $rows = @($raw | ConvertFrom-Json)
            foreach ($row in $rows) {
                $health = [string]$row.Health
                $state = [string]$row.State
                if ($health -eq "healthy") { return }
                if ($health -eq "" -and $state -match "healthy") { return }
            }
        }
        Start-Sleep -Seconds 2
    }
    Write-Error "service '$Service' did not become healthy in ${TimeoutSec}s"
    exit 1
}

Write-Host "waiting for db healthy..."
Wait-ServiceHealthy -Service "db"

$healthUrl = "http://127.0.0.1:8765/api/health"
Write-Host "waiting for api $healthUrl ..."
$sw = [Diagnostics.Stopwatch]::StartNew()
$ok = $false
while ($sw.Elapsed.TotalSeconds -lt 180) {
    try {
        $resp = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5
        if ($resp.StatusCode -eq 200 -and $resp.Content -match '"db"\s*:\s*"ok"') {
            $ok = $true
            break
        }
    } catch {
        # still starting
    }
    Start-Sleep -Seconds 2
}
if (-not $ok) {
    Write-Error "api health did not return 200 db=ok in 180s (no secrets printed)"
    exit 1
}

Write-Host "stand up:"
Write-Host "  UI      http://localhost:8765/"
Write-Host "  health  http://localhost:8765/api/health"
Write-Host "  Postgres host port 5433 (container 5432)"
exit 0
