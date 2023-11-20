param accountName string
param location string = resourceGroup().location
param tags object = {}

param databaseName string = 'Demo'
param databaseName2 string = 'KeyData'
param principalIds array = []

param containers array = [
  {
    name: 'UseCaseDefinition'
    id: 'UseCaseDefinition'
    partitionKey: '/id'
  }
]
param containers2 array = [
  {
    name: 'Temperature'
    id: 'Temperature'
    partitionKey: '/id'
  }
  {
    name: 'Model'
    id: 'Model'
    partitionKey: '/id'
  }
  {
    name: 'Prompts'
    id: 'Prompts'
    partitionKey: '/id'
  }
]

module cosmos 'core/database/cosmos/sql/cosmos-sql-db.bicep' = {
  name: 'cosmos-sql'
  params: {
    accountName: accountName
    databaseName: databaseName
    databaseName2: databaseName2
    location: location
    containers: containers
    containers2: containers2
    tags: tags
    principalIds: principalIds
  }
}


output databaseName string = cosmos.outputs.databaseName
output databaseName2 string = cosmos.outputs.databaseName2
output accountName string = cosmos.outputs.accountName
output endpoint string = cosmos.outputs.endpoint
