targetScope = 'subscription'

param environmentName string
param location string
param resourceGroupName string
param foundryAccountName string
param foundryProjectName string
param logAnalyticsWorkspaceName string
param appInsightsName string
param modelDeploymentName string

resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' existing = {
  name: resourceGroupName
}

module resources './modules/resources.bicep' = {
  name: 'patchpilot-resources'
  scope: resourceGroup
  params: {
    name: 'patchpilot'
    environmentName: environmentName
    location: location
    tags: {
      'azd-env-name': environmentName
      'demo-topic': 'memory-and-context-poisoning'
    }
    foundryAccountName: foundryAccountName
    foundryProjectName: foundryProjectName
    logAnalyticsWorkspaceName: logAnalyticsWorkspaceName
    appInsightsName: appInsightsName
    modelDeploymentName: modelDeploymentName
  }
}

output AZURE_RESOURCE_GROUP string = resourceGroup.name
output AZURE_LOCATION string = location
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.containerRegistryEndpoint
output AZURE_CONTAINER_APPS_ENVIRONMENT_NAME string = resources.outputs.containerAppsEnvironmentName
output AZURE_STORAGE_ACCOUNT_NAME string = resources.outputs.storageAccountName
output AZURE_SEARCH_SERVICE_NAME string = resources.outputs.searchServiceName
output AZURE_SEARCH_ENDPOINT string = resources.outputs.searchEndpoint
output AZURE_AI_PROJECT_ENDPOINT string = resources.outputs.foundryProjectEndpoint
output API_URL string = resources.outputs.apiUrl
output WEB_URL string = resources.outputs.webUrl
