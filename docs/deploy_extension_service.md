**Configuring and Deploying Extension-service to Cloud Run**

***Before you begin:***

1. In the Google Cloud console, on the project selector page, select or [create a Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects).\
2. [Make sure that billing is enabled for your Google Cloud project](https://cloud.google.com/billing/docs/how-to/verify-billing-enabled#console).
3. [Install](https://cloud.google.com/sdk/docs/install) the Google Cloud CLI.
4. To [initialize](https://cloud.google.com/sdk/docs/initializing) the gcloud CLI, run the following command:
```
gcloud init
```
5. To set the default project for your Cloud Run service:

```
gcloud config set project
```
6. If you are under a domain restriction organization policy [restricting](https://cloud.google.com/run/docs/authenticating/public#domain-restricted-sharing) unauthenticated invocations for your project, you will need to access your deployed service as described under [Testing private services](https://cloud.google.com/run/docs/triggering/https-request#testing-private).
7. If you are using VPC based datastore, make sure your Cloud Run service and datastore are in the same VPC network.

&nbsp;
&nbsp;

***Permissions required to deploy:***

To deploy from source, you need permissions to build, store the built container image and deploy.

You must have ONE of the following:

- Owner role
- Editor role
- The following set of roles:
  - Cloud Build Editor role
  - Artifact Registry Admin role
  - Storage Admin role
  - Cloud Run Admin role
  - Service Account User role

&nbsp;
&nbsp;

***Deployment:***

We need to deploy 2 services to Cloud Run: extension service and langchain service.

1. In the database-query-extension directory, deploy the extension service using the following command:

```
gcloud run deploy --source=./extension\_service/
```

2. For the service name, enter db-extension-service:

```
Service name (extensionservice):  db-extension-service
```

3. Disallow unauthenticated invocations if you are under a domain restriction organization policy:

```
Allow unauthenticated invocations to \[db-extension-service] (y/N)?  N 
```

4. Wait for several minutes for the deployment to finish.


