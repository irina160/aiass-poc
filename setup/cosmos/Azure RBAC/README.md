# When to use this file

Once you ran into the following error:

```python
azure.cosmos.exceptions.CosmosHttpResponseError: (Forbidden) Request blocked by Auth cosmosdb120923 : Request is blocked because principal [000000000] does not have required RBAC permissions to perform action [Microsoft.DocumentDB/databaseAccounts/readMetadata] on resource [/]. Learn more: https://aka.ms/cosmos-native-rbac.
ActivityId: a6806ad9-7ba5-43b6-94b3-11897fe19b17, Microsoft.Azure.Documents.Common/2.14.0
Code: Forbidden
Message: Request blocked by Auth cosmosdb120923 : Request is blocked because principal [000000000] does not have required RBAC permissions to perform action [Microsoft.DocumentDB/databaseAccounts/readMetadata] on resource [/]. Learn more: https://aka.ms/cosmos-native-rbac.
ActivityId: a6806ad9-7ba5-43b6-94b3-11897fe19b17, Microsoft.Azure.Documents.Common/2.14.0
```

This means you do not have the necessary rights to perform this action. In order to grant you this access an administrator has to grant you these rights.

# As an Admin, how do I grant rights for CosmosDB?

Login to you Azure CLI using `az login`. Once logged in execute the following command, replacing the values with your correct values:

```shell
resourceGroupName='<myResourceGroup>'
accountName='<myCosmosAccount>'
az cosmosdb sql role definition create --account-name $accountName --resource-group $resourceGroupName --body setup/cosmos/Azure\ RBAC/CosmosDBreadonly.json
```

Next grant the write access rights:

```shell
az cosmosdb sql role definition create --account-name $accountName --resource-group $resourceGroupName --body setup/cosmos/Azure\ RBAC/CosmosDBwrite.json
```

Now you need to fetch the IDs from the role assignments using the following command:

```shell
az cosmosdb sql role definition list --account-name $accountName --resource-group $resourceGroupName
```

Now that you have the IDs you can assign them to your own principal ID (the ID is also in your error message from above!).

```shell
resourceGroupName='<myResourceGroup>'
accountName='<myCosmosAccount>'
readOnlyRoleDefinitionId='<roleDefinitionId>' # as fetched above
# For Service Principals make sure to use the Object ID as found in the Enterprise applications section of the Azure Active Directory portal blade.
principalId='<aadPrincipalId>'
az cosmosdb sql role assignment create --account-name $accountName --resource-group $resourceGroupName --scope "/" --principal-id $principalId --role-definition-id $readOnlyRoleDefinitionId
```
