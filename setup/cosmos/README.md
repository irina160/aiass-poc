# How this works (ONLY LOCAL)

This script fills the CosmosDB databases with test data. Be aware, if this data is not in there, then you cannot access the application! You can run this script by running .\cosmosdb_setup.ps1 <cosmosservice> <apikey>. Service and key for CosmosDB can be found at https://portal.azure.com/.

# CosmosDB upload script

The script needs an endpoint and an apikey as given arguments to connect to cosmosDB.
The directories in the "data" folder are considered to be the database names and contain json files. The names of the json files are considered to be the container names and contain items which are to be uploaded to the containers. If a database/container/item already exists it is replaced by the new data.
