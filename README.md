# 🚀 Google Cloud Deployment Template 🚀

Use this template for easily deploy project within the repo to google cloud.

> If you just want to quickly get the most important stuff from here, scroll through the readme and watch out for 🚨 and ⚠️ Signs!

## Table of contents

---

- [🔧 Prerequisites](#Prerequisites)
- [⚠️ Caution](#Caution)
- [🧰 Configuring config.yaml](#config-yaml)
- [🧭 How to deploy a...](#how-to)
  - [Service / Job / CronJob](#Service)
    - [Important](#notices-services)
    - [Build logs](#Build-Logs)
    - [Run Logs && Status of Containers](#run-status)
    - [Restarting](#Restarting)
    - [Environment Variables & Preconfigs](#env)
    - [Databases](#Databases)
    - [Resources](#Resources)
    - [Persistence](#Persistence)
      - [Buckets](#Buckets)
      - [SSD Volumes](#SSD-Volumes)
  - [Website](#Website)
    - [Bucket content](#bucket-content)
- [🔭 Making it public](#make-it-public)

<a name="Prerequisites"></a>

## 🔧 Prerequisites

---

If you are using [VS CODE](https://code.visualstudio.com/), please
install [YAML Validator](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
for getting assistance on configuring `config.yaml`.

<a name="Caution"></a>

## ⚠️ Caution / FAQs:

---

### General

- Don't change files in `.github` folder
- Please don't change repo name when using this template! (use `settings.projectname` instead)
  - If change is necassery delete the whole application and its resources before
- Check, if `config.yaml` is configured properly
- You can delete values from `config.yaml`, which you don't want to set (except required ones)
- Deployments will just be triggered on `develop` or `live` branch

### Service

- When deploying a service (e.g. Webserver/API) make sure that
  - Your application runs on host `0.0.0.0`
  - The port of your application is `3000`
- On `develop` STAGE (/branch) your service will be basic auth secured by default.
  - To reset basic auth set `setttings.inSecure:true`
- If your service/job behaves strange on cloud, try to just start your image/docker in sleeping mode:
  - set `run.command: "sleep 1h"`
  - connect to your service via description on your application page
  - start your application from there and debug
  - ⚠️ Make sure to update the changes to your repository
- If you need to install some other tools/binaries on your "machine", use the `image.preparationCommand` setting
  - e.g. `image.preparationCommand: "apk add --no-cache curl tar bash procps"`
  - Do not prepend `RUN` statement. This is added automatically!
  - If you wish to add tools/binaries via an install script, use the option within `build.command`
- If you want to use a custom image (`image.imageFrom`), so no preset is selected, make sure, that a certification authority ( [ca-certificates](https://packages.debian.org/sid/ca-certificates) ) are installed (for example via `preparationCommand`)
- If a service can't be deleted or stucks in `Terminating` state use following command:
  - `kubectl delete pod <PODNAME> --force --grace-period=0 -n <protected/standard (DEV/LIVE)>`

### Website

- Currently just builds with node are available on type `website`

<a name="config-yaml"></a>

## 🧰 Configuring config.yaml

---

The `config.yaml` file is the most important part to configure your deployment and hosting. You have plenty of options
to customize the output:

```yaml
isEnabled: # [REQUIRED] Whether to trigger deployments on push
image:
  preset: # [OPTIONAL] Environment to build and run application: node, java, python
  preparationCommand: # [OPTIONAL] used for downloading additional OS packages before building and running your app. These will be available during build and run.
  imageFrom: #  [OPTIONAL/REQUIRED]  If no preset is used this is required, e.g. `ubuntu`
  ignore: # [OPTIONAL] Ignore some files / Folders which are not used for running/building the app
build:
  command: # [OPTIONAL] Command for installing application dependencies and building your app, If just upload eg. static files, this can be skipped
  outputFolder: # [OPTIONAL] Folder of your application. Empty for using all of root folder. If set, all other folders/files will be ignored
run:
  command: # [OPTIONAL/REQUIRED] Command for running your app, not required if type is website
  envs: # [OPTIONAL] Environment Variables to inject (will be available during build and as runtime environment variable)
    - name: # [REQUIRED] Environment Variable name
      value: # [REQUIRED] Environment Variable value
settings:
  projectName: # [OPTIONAL] Use different name as repository name (will be linked to repoName within metaData to prevent multiple project with same name)
  type: # [REQUIRED] website/service/job/cronjob - for details see how to section
  schedule: # [OPTIONAL/REQUIRED] crontab schedule - required if cronjob type is set
  persistentBucket: # [OPTIONAL] Use persistence layer for your service by providing the created bucket-name (see persistence layer section)
  persistentVolume: # [OPTIONAL] Use persistence layer with real file system
    mountPath: # [OPTIONAL] Where your volume shoud be mounted (accessable); default: "/data/storage/"
    size: # [OPTIONAL] Size in Gigabyte
  database: # [OPTIONAL] Use database for this service
    type: # [REQUIRED] Type of database (sql/elasticsearch)
    frontend: # [OPTIONAL] Also create kibana frontend - default is false
    size: # [OPTIONAL] Size in Gigabyte
  replicas: # [OPTIONAL] How many parallel instances of your app should be started (default is 1)
  resources: # [OPTIONAL] Settings on application resourcesA
    requests: # [OPTIONAL] What is the appplication requesting at max
      cpu: # see https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu
      memory: # see https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory
    limits: # [OPTIONAL] What is the appplications limit - important to get warnings
      cpu: # see https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-cpu
      memory: # see https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory
  inSecure: # [OPTIONAL] Disable basic auth on DEV - default is false (so access will be restricted, you can find credentials in 1Password via `Google Cloud DEV`
```

<a name="how-to"></a>

## 🧭 How to deploy a...

---

Just push your changes to `develop` or `live` branch and see your application running on Google Cloud.

There are currently two types of deployments / hostings:

<a name="Service"></a>

### Service / Job / CronJob

##### Important Notices:

> 🚨 Keep in mind that a service/job/cronjob itself is stateless. After each build retrigger (git push), the container, where the service/job lives in, is newly created. To have persistence within the container please refer to the <a name="Persistence">persistence section</a>.

<a name="Build-Logs"></a>

A service (type: `service`), a job (type: `job`) or a cronjob (type: `cronjob`) is a fully managed application which has a defined runtime (via `image.imageFrom`
or `image.preset`).

> 💡 You can think of it as a mini virtual machine with its own scope.

<a name="service-desc"></a>

##### Service:

A Service will have an external address, which can be accessed via:

- `develop`: https://`<projectName>`.brdata-dev.de
- `live`: https://`<projectName>`.interaktiv.br.de

It will scale itself (resources like RAM, CPU, ...) with the demand of the service itself. Also, when getting high
traffic it will route automatically to the less occupied service instance.

> 🚨 The default port of your running and exposing application should run on host `0.0.0.0` and port `3000`

<a name="job-desc"></a>

##### Job:

A Job just does some stuff internally and then shuts down.

<a name="cronjob-desc"></a>

##### CronJob:

A CronJob is like a job so just does some stuff internally and then shuts down at given schedule (within `config.yaml` -> `settings.schedule`)

<a name="notices-services"></a>

#### Build Logs

While building the service you can see a log message within the actions tab at the current repository, which tells you
the URL for accessing build logs.

<a name="run-status"></a>

#### Run Logs && Status of Containers

The logs of your running container will also be displayed within the actions tab at the current repository, after it
build successfully. When clicking on the link:

- `develop`: https://console.cloud.google.com/kubernetes/deployment/europe-west1/dev/protected/`<projectName>`-deployment/overview?project=brdata-dev&supportedpurview=project
- `live`: https://console.cloud.google.com/kubernetes/deployment/europe-west1/dev/standard/`<projectName>`-deployment/overview?project=brdata-live&supportedpurview=project

You then can navigate to the `LOGS` Tab.

<a name="Restarting"></a>

#### Restarting

Restarting can be done either by pushing a new state to the repository or via Google Cloud Console.

As Google K8S currently doesn't have a "Restart" Button for the container you have to do it manually:

- Go to the Deployment page (see Run Logs && Status of Containers )
- Go to YAML tab and click the "Edit" Button on top tabs
- Add / Remove any unnecessary `env` entry, which does nothing, eg:
  - ```yaml
    - name: Test
      value: test
    ```
- Hit Save Button and wait for restarting

<a name="env"></a>

#### Environment Variables

If you want to provide runtime variables you can add them in the `config.yaml` in the described way.

Default environment variables are:

| NAME             | DESCRIPTION                                           | PROVIDED IF...               |
| ---------------- | ----------------------------------------------------- | ---------------------------- |
| STAGE            | The current stage (`develop`/`live`)                  | always                       |
| HOST             | The host, where the service will run on               | always                       |
| NAME             | The project name that is used                         | always                       |
| PORT             | The default port of the service (⚠ should be `3000`!) | always                       |
| URL              | The final URL of the service                          | always                       |
| DATABASE_ADDRESS | `IP:PORT` of your database                            | database is selected         |
| VOLUME_PATH      | Folder, where bucket data is provided                 | persistentBucket is provided |

If you have secrets that should be added as environment variables please add them via:

- `develop`: [DEV - Secret Manager]()
- `live`: [LIVE - Secret Manager]()

> ⚠️ Keep in mind that your image should have CA installed, see <a name="docker">docker notes</a>

Copy the name of the created Secret (here referred as <my-secret>) and add it to the `config.yaml`:

```yaml
envs:
  - name: MY_SECRET
    value: "sm://{{.projectId}}/<my-secret>"
```

> ⚠️ The value for a secret has to have the prefix `sm://{{.projectId}}/` so please don't change that! `{{.projectId}}` will be automatically aggregated to the current environment (develop/live)

> ⚠️ Use single quotes when setting secret manager references!

<a name="Databases"></a>

#### Databases

If you want to access your own database, simply add database prop within the config.yaml. For this set the type of the
database you want to deploy:

- elasticsearch
- sql

For also creating a frontend for the database simply add frontend: true to the database property.

Example:

```yaml
# ...
settings:
  database:
    type: elasticsearch
    frontend: true
    size: 5 # Gigabyte
```

> To access the database via your service use the environment variable: `DATABASE_ADDRESS` to get the `IP:Port` of your database
  
##### Existing database connection
  
If you want to connect to an existing database (already created by another service).
Just add the application name of existing database (without type "-postgres"/"-elasticsearch"! in the name).
You can configure it like:

```yaml
# ...
settings:
  database:
    type: elasticsearch 
    existingName: application-that-created-the-database
```

#### Resources

You can also specify how many resources your application may need. You can specify three types.

- memory
- cpu
- gpu

Memory can be assigned with units `Gi`,`Mi`,`G`,`M` where the i at the end means bibytes.
CPU can be requested as Cores of a CPU (0.5 is half core)
GPU (use `1` as value) will use a NVIDEA T4 Grpahic Card (https://www.nvidia.com/en-us/data-center/tesla-t4/)

Example:

```yaml
# ...
settings:
  resources:
    cpu: 25m #(0.025 cores)
    memory: 64Mi
```

<a name="Persistence"></a>

#### Persistence

If you want to have a persistence layer to always have access to some specific files within multiple service instances,
you can add an option in the `config.yaml`.

For just want to save files (e.g. for backup) you can use a bucket, which has no limitations for storage size.

> ⚠️ Buckets have problems with nested folder structure. So please be aware, that when using buckets, keep clean and narrow folder structure

If you want to have a faster volume you can use ssd volumes. There you have to specify the size (unit: `Gi`)

<a name="Buckets"></a>

##### Buckets

For that just add `persistentBucket: "<BUCKET_NAME>"`.

> ⚠️ The bucket with the name `<BUCKET_NAME>` should already be manually created within the correct Google Cloud project!

Before deploying the service make sure you have created the bucket (`<BUCKET_NAME>`) within the Google Storage:

- `develop`: [DEV-Storage](https://console.cloud.google.com/storage/browser?forceOnBucketsSortingFiltering=false&project=brdata-dev&supportedpurview=project&prefix=&forceOnObjectsSortingFiltering=false)
- `live`: [LIVE-Storage](https://console.cloud.google.com/storage/browser?forceOnBucketsSortingFiltering=false&project=brdata-live&supportedpurview=project&prefix=&forceOnObjectsSortingFiltering=false)

⚠ When creating the bucket, ensure that the region is `europe-west3`!

> You can access the persistent storage within the service via: <b>/data/storage/\*</b> - This also provided as environment Variable see <a name="env">here</a>

<a name="SSD-Volumes"></a>

##### SSD Volumes

SSD Volumes provide a real file system.
You can have a shared volume (~250Mib/s) which can be mounted by multiple Applications the same time.
Or a non-shared volume (~2Gib/s) which is just usable from one application.

Example config.yaml:

```yaml
# ...
settings:
  persistentVolume:
    shared: true
    size: 1 # Gigabytes
    mountPath: /data/test/
```

You can also mount an already existing volume by using:

```yaml
# ...
settings:
  persistentVolume:
    existingName: "repo-name" # Without the "-(ssd)-volume" appendix
    mountPath: /data/test/
```

<a name="Website"></a>

### Website

To create a static website just set the type within `config.yaml` to `website`.

Your Website will be hosted via:

- `develop`: https://interaktiv.brdata-dev.de/<projectName>
- `live`: https://interaktiv.br.de/<projectName>

> On develop branch, the website will be secured automatically. If you want to set the basic auth for that, please add a new repo secret (within settings/security/secrets/actions): `BASIC_PW` with following content

```shell
u:YOUR_USER_NAME
p:YOUR_PW
```

<a name="bucket-content"></a>

#### Bucket content

The website will be served via a Google Storage Bucket. You can view the content via:

- `develop`: [DEV-Bucket](https://console.cloud.google.com/storage/browser/br-dev;tab=objects?forceOnBucketsSortingFiltering=false&project=brdata-dev&supportedpurview=project&prefix=&forceOnObjectsSortingFiltering=false)
- `live`: [LIVE-Bucket](https://console.cloud.google.com/storage/browser/interaktiv.br.de;tab=objects?forceOnBucketsSortingFiltering=false&project=brdata-live&supportedpurview=project&prefix=&forceOnObjectsSortingFiltering=false)

<a name="make-it-public"></a>

## 🔭 Making it public

If you want to make your repository public add following changes to your actions settings:

### Actions

1. Go to repository `Settings`
1. Click `Actions -> Gerneral` Tab
1. Select `Allow br-data actions and reusable workflows`
1. Hit save

> ⚠️ This is important, that nobody can add a custom action and may read secrets within the provided custom action

### Branch Protection

1. Go to repository `Settings`
1. Click `Branches` Tab
1. Hit `Add Rule` (for `develop` and `live`)
1. Select `Require a pull request before merging` and the sub-option `Require approvals`
1. Hit save
