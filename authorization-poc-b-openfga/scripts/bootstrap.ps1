param([string]$StoreName="poc-b-openfga",[string]$ApiUrl="http://localhost:8080")
$ErrorActionPreference="Stop"
Write-Host "Waiting for OpenFGA..."
for($i=0;$i-lt 30;$i++){try{Invoke-RestMethod "$ApiUrl/health"|Out-Null;break}catch{Start-Sleep 2}}
$storeBody=@{name=$StoreName}|ConvertTo-Json
$store=Invoke-RestMethod "$ApiUrl/stores" -Method Post -ContentType "application/json" -Body $storeBody
$storeId=$store.id
Write-Host "STORE_ID=$storeId"
# Convert DSL to API JSON with the official CLI
docker run --rm -v "${PWD}:/work" openfga/cli model transform --file /work/model/model.fga | Out-File -Encoding utf8 model/model.json
$modelJson=Get-Content model/model.json -Raw
# Strip possible BOM from PowerShell output
$modelJson=$modelJson.TrimStart([char]0xFEFF)
$model=Invoke-RestMethod "$ApiUrl/stores/$storeId/authorization-models" -Method Post -ContentType "application/json" -Body $modelJson
$modelId=$model.authorization_model_id
Write-Host "MODEL_ID=$modelId"
$env:FGA_STORE_ID=$storeId; $env:FGA_MODEL_ID=$modelId
python app/openfga_client.py write-tuples --store-id $storeId --model-id $modelId --tuples data/tuples.jsonl --batch-size 100
Write-Host "Bootstrap complete."
Write-Host "FGA_STORE_ID=$env:FGA_STORE_ID"
Write-Host "FGA_MODEL_ID=$env:FGA_MODEL_ID"
