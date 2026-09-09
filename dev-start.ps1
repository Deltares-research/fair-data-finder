<#
.SYNOPSIS
    One-shot dev environment startup for Fair Data Finder.

.DESCRIPTION
    - Prompts for the DMS token used to authenticate against the source STAC API,
      and the STAC domain to pull data from. Nothing is cached to disk.
    - Builds and starts the docker compose stack (detached).
    - Waits for http://localhost:8000/api and http://localhost:3000 to return HTTP 200.
    - Populates the local pgSTAC database from the source STAC API.
    - Verifies the database has data via a direct Postgres row-count query
      (pgSTAC collections/items), since /api/search requires an SSO session.
#>

$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot
$FdfDir = Join-Path $RepoRoot "fair-data-finder"
$DefaultStacDomain = "https://deltares-fairdata.com"

function ConvertFrom-SecureStringPlain {
    param([Security.SecureString]$Secure)
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

function Get-DmsToken {
    $secure = Read-Host "Enter your DMS token (used to authenticate against the source STAC API)" -AsSecureString
    $token = ConvertFrom-SecureStringPlain $secure
    if ([string]::IsNullOrWhiteSpace($token)) {
        Write-Warning "No DMS token provided; the migration will run without authentication."
        $token = ""
    }
    return $token
}

function Get-StacSourceUrl {
    $input = Read-Host "STAC domain to migrate data from [$DefaultStacDomain]"
    $domain = if ([string]::IsNullOrWhiteSpace($input)) { $DefaultStacDomain } else { $input }
    $domain = $domain.TrimEnd("/")
    return "$domain/api"
}

function Wait-ForOk {
    param([string]$Name, [string]$Url, [int]$MaxAttempts = 60, [int]$DelaySeconds = 3)

    Write-Host "`nWaiting for $Name ($Url) ..." -ForegroundColor Cyan
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        $code = & curl.exe -s -L -o NUL -w "%{http_code}" --max-time 10 $Url 2>$null
        if ($code -eq "200") {
            Write-Host "$Name is up." -ForegroundColor Green
            return $true
        }
        Write-Host "." -NoNewline
        Start-Sleep -Seconds $DelaySeconds
    }
    Write-Host ""
    return $false
}

function Test-DatabaseHasData {
    $collectionsRaw = docker compose exec -T postgres psql -U postgres -d postgres -tAc "SELECT count(*) FROM pgstac.collections;" 2>$null
    $itemsRaw = docker compose exec -T postgres psql -U postgres -d postgres -tAc "SELECT count(*) FROM pgstac.items;" 2>$null

    $collections = 0
    $items = 0
    [int]::TryParse(($collectionsRaw -join "").Trim(), [ref]$collections) | Out-Null
    [int]::TryParse(($itemsRaw -join "").Trim(), [ref]$items) | Out-Null

    Write-Host "  collections: $collections, items: $items"
    return ($collections -gt 0 -or $items -gt 0)
}

Write-Host "=== Fair Data Finder dev environment ===" -ForegroundColor Cyan

$dmsToken = Get-DmsToken
$stacUrl = Get-StacSourceUrl

if (-not (Test-Path $FdfDir)) {
    Write-Error "Could not find fair-data-finder folder at $FdfDir"
    exit 1
}

Push-Location $FdfDir
try {
    Write-Host "`nBuilding and starting docker compose stack (detached) ..." -ForegroundColor Cyan
    docker compose up --build -d
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up failed. Is Docker Desktop running?"
    }

    $backendOk = Wait-ForOk -Name "backend (http://localhost:8000/api)" -Url "http://localhost:8000/api"
    $frontendOk = Wait-ForOk -Name "frontend (http://localhost:3000)" -Url "http://localhost:3000"

    if (-not $backendOk) {
        Write-Warning "Backend did not respond with 200 in time. Check logs with: docker compose logs backend"
    }
    if (-not $frontendOk) {
        Write-Warning "Frontend did not respond with 200 in time. Check logs with: docker compose logs frontend"
    }

    if (-not $backendOk) {
        Write-Warning "Skipping database population."
    } else {
        Write-Host "`nPopulating database from $stacUrl ..." -ForegroundColor Cyan
        # The migration script's --database-url default points at "localhost", which
        # inside the backend container is the container itself, not the postgres
        # service. Build the correct URL from the container's own PG* env vars
        # (already loaded from backend/.env) instead of hardcoding credentials here.
        docker compose exec -T `
            -e SOURCE_URL=$stacUrl `
            -e DMS_TOKEN=$dmsToken `
            backend bash -c 'uv run python scripts/migrate_to_pgstac.py --source-url "$SOURCE_URL" --dms-token "$DMS_TOKEN" --database-url "postgresql://$PGUSER:$PGPASSWORD@$PGHOST:$PGPORT/$PGDATABASE"'
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Migration script exited with errors, see output above."
        } else {
            Write-Host "Database populated." -ForegroundColor Green
        }

        Write-Host "`nChecking database has data ..." -ForegroundColor Cyan
        if (Test-DatabaseHasData) {
            Write-Host "Database contains data." -ForegroundColor Green
        } else {
            Write-Warning "pgSTAC has zero collections and items. The database is empty."
        }
    }
} finally {
    Pop-Location
}

Write-Host "`n=== Ready ===" -ForegroundColor Cyan
Write-Host "Frontend:      http://localhost:3000"
Write-Host "Backend API:   http://localhost:8000/api/"
Write-Host "Swagger docs:  http://localhost:8000/api/api.html"
Write-Host "Via proxy:     https://localhost  (accept self-signed cert once)"
Write-Host "`nStop the stack with: docker compose down (run from fair-data-finder\)"
