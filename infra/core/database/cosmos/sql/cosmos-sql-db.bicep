metadata description = 'Creates an Azure Cosmos DB for NoSQL account with a database.'
param accountName string
param databaseName string
param databaseName2 string
param location string = resourceGroup().location
param tags object = {}

param containers array = []
param containers2 array = []
param principalIds array = []

module cosmos 'cosmos-sql-account.bicep' = {
  name: 'cosmos-sql-account'
  params: {
    name: accountName
    location: location
    tags: tags
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2022-05-15' = {
  name: '${accountName}/${databaseName}'
  properties: {
    resource: { id: databaseName }
  }

  resource list 'containers' = [for container in containers: {
    name: container.name
    properties: {
      resource: {
        id: container.id
        partitionKey: { paths: [ container.partitionKey ] }
      }
      options: {}
    }
  }]

  dependsOn: [
    cosmos
  ]
}

resource database2 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2022-05-15' = {
  name: '${accountName}/${databaseName2}'
  properties: {
    resource: { id: databaseName2 }
  }

  resource list 'containers' = [for container in containers2: {
    name: container.name
    properties: {
      resource: {
        id: container.id
        partitionKey: { paths: [ container.partitionKey ] }
      }
      options: {}
    }
  }]

  dependsOn: [
    cosmos
  ]
}

module roleDefinition 'cosmos-sql-role-def.bicep' = {
  name: 'cosmos-sql-role-definition'
  params: {
    accountName: accountName
  }
  dependsOn: [
    cosmos
    database
    database2
  ]
}

// We need batchSize(1) here because sql role assignments have to be done sequentially
@batchSize(1)
module userRole 'cosmos-sql-role-assign.bicep' = [for principalId in principalIds: if (!empty(principalId)) {
  name: 'cosmos-sql-user-role-${uniqueString(principalId)}'
  params: {
    accountName: accountName
    roleDefinitionId: roleDefinition.outputs.id
    principalId: principalId
  }
  dependsOn: [
    cosmos
    database
    database2
  ]
}]

output accountId string = cosmos.outputs.id
output accountName string = cosmos.outputs.name
output databaseName string = databaseName
output databaseName2 string = databaseName2
output endpoint string = cosmos.outputs.endpoint
output roleDefinitionId string = roleDefinition.outputs.id
