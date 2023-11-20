$cosmosservice=$args[0]
$apikey=$args[1]

# Check if required arguments are provided
if (-Not $cosmosservice -Or -Not $apikey) {
    Write-Host "Usage: .\cosmosdb_setup.ps1 <cosmosservice> <apikey>"
    Exit
}

Write-Host "cosmosservice: " $cosmosservice
Write-Host "apikey: " $apikey

Write-Host 'Creating python virtual environment "setup/cosmos/.venv"'
python -m venv .\setup\cosmos\.venv

Write-Host 'Installing dependencies from "requirements.txt" into virtual environment'
.\setup\cosmos\.venv\Scripts\python -m pip install -r .\setup\cosmos\requirements.txt

Write-Host 'Running "upload_cosmos_data.py"'
.\setup\cosmos\.venv\Scripts\python .\setup\cosmos\upload_cosmos_data.py --cosmosservice $cosmosservice --apikey $apikey
