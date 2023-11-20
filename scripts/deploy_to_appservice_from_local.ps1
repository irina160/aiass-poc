param(
   [Parameter(Mandatory=$true)]
   [string]$resourceGroupName,
   [Parameter(Mandatory=$true)]
   [string]$appName
)

$workspacePath = $PWD.Path
$backendPath = Join-Path $workspacePath "app/backend"
$frontendPath = Join-Path $workspacePath "app/frontend"
$deploymentPath = Join-Path $workspacePath "app/deployment"
$zipFilePath = Join-Path $deploymentPath "app.zip"

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
  # fallback to python3 if python not found
  $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

$azCmd = Get-Command az -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Install requirements"
Write-Host ""

Start-Process -FilePath ($pythonCmd).Source -ArgumentList "-m pip install pyclean==2.7.5" -Wait -NoNewWindow

Write-Host ""
Write-Host "Check for Login status"
Write-Host ""

$accountinfo = Start-Process -FilePath ($azCmd).Source -ArgumentList "account show -o json" -Wait -NoNewWindow

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Login to Azure manually"
    Write-Host ""

    Start-Process -FilePath ($azCmd).Source -ArgumentList "login" -Wait -NoNewWindow
}
Write-Host ""
Write-Host "Login to Azure successfull"
Write-Host ""

Write-Host ""
Write-Host "Go to frontend and build solution"
Write-Host ""

cd $frontendPath

npm run build

Write-Host ""
Write-Host "Build successfull"
Write-Host ""

Write-Host ""
Write-Host "Create deployment dir"
Write-Host ""

New-Item -ItemType Directory -Path $deploymentPath

Write-Host ""
Write-Host "Copy files from backend to deployment"
Write-Host ""

cd $backendPath

Copy-Item -Path * -Destination $deploymentPath -Recurse

Write-Host ""
Write-Host "Go to deployment folder"
Write-Host ""

cd $deploymentPath

Write-Host ""
Write-Host "Cleanup deployment dir"
Write-Host ""

Start-Process -FilePath ($pythonCmd).Source -ArgumentList "-m pyclean ." -Wait -NoNewWindow

Write-Host ""
Write-Host "Created zip file $zipFilePath"
Write-Host ""

Compress-Archive -Path * -DestinationPath $zipFilePath

Write-Host ""
Write-Host "Deploy to Azure App Service: $appName"
Write-Host ""

Start-Process -FilePath ($azCmd).Source -ArgumentList "webapp config appsettings set --resource-group $resourceGroupName --name $appName --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true" -Wait -NoNewWindow

Start-Process -FilePath ($azCmd).Source -ArgumentList "webapp deploy --resource-group $resourceGroupName --name $appName --src-path $zipFilePath --async true --restart true" -Wait -NoNewWindow

Write-Host ""
Write-Host "Cleanup requirements"
Write-Host ""

Start-Process -FilePath ($pythonCmd).Source -ArgumentList "-m pip uninstall pyclean --yes" -Wait -NoNewWindow

Write-Host ""
Write-Host "Deployment successfull. Delete $deploymentPath"
Write-Host ""

Remove-Item -LiteralPath $deploymentPath -Force

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Something went wrong when deleting $deploymentPath. Please do that manually!"
    Write-Host ""
}