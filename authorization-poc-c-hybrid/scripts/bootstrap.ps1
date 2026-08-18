param(
    [int]$HealthRetries = 30,
    [int]$HealthDelaySeconds = 2,
    [int]$BatchSize = 100
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

$OpenFgaBaseUrl = "http://localhost:8091"
$OpaBaseUrl = "http://localhost:8182"
$GatewayBaseUrl = "http://localhost:8090"
$ModelFile = Join-Path $ProjectRoot "openfga\model\phase1-aligned-model.json"
$TupleFile = Join-Path $ProjectRoot "data\tuples.jsonl"

function Wait-HttpHealth {
    param(
        [string]$Name,
        [string]$Url
    )

    for ($i = 1; $i -le $HealthRetries; $i++) {
        try {
            $response = Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec 5
            if ($null -ne $response) {
                Write-Host "[OK] $Name is healthy: $Url"
                return
            }
        } catch {
            Write-Host "[WAIT] $Name not ready ($i/$HealthRetries)"
        }

        Start-Sleep -Seconds $HealthDelaySeconds
    }

    throw "$Name did not become healthy: $Url"
}

Write-Host ""
Write-Host "=== POC-C Hybrid Bootstrap ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot"
Write-Host ""

Write-Host "[1/6] Checking Docker services..." -ForegroundColor Yellow
docker compose ps
if ($LASTEXITCODE -ne 0) {
    throw "docker compose ps failed."
}

Write-Host "[2/6] Waiting for OpenFGA, OPA and Gateway..." -ForegroundColor Yellow
Wait-HttpHealth -Name "OpenFGA" -Url "$OpenFgaBaseUrl/healthz"
Wait-HttpHealth -Name "OPA" -Url "$OpaBaseUrl/health"
# Gateway depends on FGA/OPA and needs the store/model IDs, so it may not be
# healthy yet. We only check FGA/OPA before provisioning.

Write-Host "[3/6] Creating a fresh OpenFGA store..." -ForegroundColor Yellow

$storeBody = @{
    name = "poc-c-hybrid"
} | ConvertTo-Json

$store = Invoke-RestMethod `
    -Uri "$OpenFgaBaseUrl/stores" `
    -Method POST `
    -ContentType "application/json" `
    -Body $storeBody

$StoreId = $store.id

if ([string]::IsNullOrWhiteSpace($StoreId)) {
    throw "OpenFGA did not return a store ID."
}

Write-Host "STORE_ID=$StoreId" -ForegroundColor Green

Write-Host "[4/6] Creating the Phase-1-aligned OpenFGA authorization model..." -ForegroundColor Yellow

if (-not (Test-Path $ModelFile)) {
    throw "Model file not found: $ModelFile"
}

$modelBody = Get-Content $ModelFile -Raw

$model = Invoke-RestMethod `
    -Uri "$OpenFgaBaseUrl/stores/$StoreId/authorization-models" `
    -Method POST `
    -ContentType "application/json" `
    -Body $modelBody

$ModelId = $model.authorization_model_id

if ([string]::IsNullOrWhiteSpace($ModelId)) {
    throw "OpenFGA did not return an authorization model ID."
}

Write-Host "MODEL_ID=$ModelId" -ForegroundColor Green

Write-Host "[5/6] Saving POC-C environment variables..." -ForegroundColor Yellow

$envFile = @"
FGA_STORE_ID=$StoreId
FGA_MODEL_ID=$ModelId
"@

Set-Content -Path (Join-Path $ProjectRoot ".env") -Value $envFile -Encoding utf8

Write-Host "[5/6] Loading Phase-1 relationship tuples..." -ForegroundColor Yellow

if (-not (Test-Path $TupleFile)) {
    throw "Tuple file not found: $TupleFile"
}

python scripts\load_phase1_tuples.py `
    --base-url $OpenFgaBaseUrl `
    --store-id $StoreId `
    --model-id $ModelId `
    --tuples $TupleFile `
    --batch-size $BatchSize

if ($LASTEXITCODE -ne 0) {
    throw "Tuple loading failed."
}

Write-Host "[6/6] Recreating the hybrid gateway with the generated IDs..." -ForegroundColor Yellow

docker compose up -d --force-recreate gateway

if ($LASTEXITCODE -ne 0) {
    throw "Failed to recreate gateway."
}

Wait-HttpHealth -Name "Gateway" -Url "$GatewayBaseUrl/health"

Write-Host ""
Write-Host "=== Bootstrap complete ===" -ForegroundColor Green
Write-Host "OpenFGA Store ID : $StoreId"
Write-Host "OpenFGA Model ID : $ModelId"
Write-Host "Expected tuples  : 365596"
Write-Host "Environment file : .env"
Write-Host ""
Write-Host "Next:"
Write-Host "  Import the Postman collection/environment."
Write-Host "  Run the functional OpenFGA, OPA and Hybrid requests."
Write-Host ""
