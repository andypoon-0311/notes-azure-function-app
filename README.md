# notes-azure-function-app
Simple function app in python to store notes using azure python sdk v2.

**Click Here To Watch a Demo, Will Redirect To Youtube**
<p align="center">
  <a href="https://youtu.be/LMVBpxSYq-s">
    <img src="https://img.youtube.com/vi/LMVBpxSYq-s/0.jpg" alt="Watch the demo" width="70%">
  </a>
</p>

The function app is connected to Azure Table Storage so that data may persist on stable storage rather than living only in memory.

## Helpers

**get_table_service_client** connects to the storage account using the function app's system assigned managed identity. In the code you may see "STORAGE_ACCOUNT" as the value for the variable **account_name**. "STORAGE_ACCOUNT" is just the name of the environment variable in azure that contains the name of the target storage account, just as if you were using a local .env file to store a key to a resource. It then proceeds to try and get the **table_client**, following that it attempts to create the table and if it already exists it does nothing. The return value is **table_client**.

**query_notes** gets a reference to the table by calling **get_table_service_client**. If no title is passed then it will return all entities. If a title is provided this helper will return the specified entity by using the partition_key "Notes" (Notes is the only partition key that exists in this case) and the row_key (title converted to lower). If nothing is found it will return none.

**query_notes_id** begins similarily to **query_notes**. It attempts to get a reference to the table by calling **get_table_service_client**. Because I have elected to make title the row_key, I must iterate through all entities if I wish to retrieve notes with the **note_id**. The purpose of this helper function is to provide flexibility to the end user in GET operations. Generally the row_key is a numeric value, but in this use case, I thought it would make more sense to retrieve notes by their title, rather than a numeric value that has nothing to do with the contents of the stored note. In any case, users may elect to utilize **note_id** instead of title when attempting to retrieve stored notes.

**create_note** inserts new note entities into Azure Table Storage. It takes three parameters, title (required), category, and data. Title being the only required parameter, the function initializes category and data to None. The function begins by checking for a title value, if one is not provided a Null value will immediately be returned. After this check, a reference is retrieved to the Azure Table Storage resource in a same manner as above. The variable now contains the datetime.now() value in isoformat so that it may be serializable by the function app. The row_key is immediately provided the value of *title.lower()*. Azure Table Storage already checks for a duplicate row and partition key combination but returns an internal server error. Error handling is included in this helper to return a more verbose message when there is a duplicate title. If a title already exists, it will return "exists", which will later be used in the POST endpoint. After error handling, the note is assigned a *note_id*. If there are no entities in the table, the note will be assigned **1**, otherwise it will be assigned the max value + 1. The schema is then defined, and if the execution reaches this point the note will be created and returned.

**get_api_key** provides a consistent way for the function app to retrieve the api key from the key vault for comparison with the user provided api key. It is using the function app's managed identity with *DefaultAzureCredential()*. The url of the key vault is stored as an environment variable *KEY_VAULT_URL*. Managed identity and the key vault url are used in combination to provide the **client** variable with *SecretClient()*. The secret value (api key) is returned from this function.

**validate_api_key** this function does the actual api key comparison. A http request the function app is a required parameter. The function extracts the value of the "x-functions_key" http header. It then calls **get_api_key** to retrieve the correct key from the key vault. The return value is boolean, it returns the results of the comparison between the user provided api key and the api key retrieved from the key vault.

NOTE: Azure functions using the python v2 sdk also supports the "code" header as the key for the key value pair. However, in this function app only "x-functions-key" is supported due to having to extract the user provided api key from the request for comparision with the key stored in the key vault.

## Endpoints

The endpoints all follow a similar structure besides **countNotes**. **countNotes** just calls the **query_notes** and stores it in *entity* as a list, and returns the length or number of entities in the Azure Storage Table. The structure was obtained from Microsoft's "Developer Reference Guide" and I did not deviate much.

https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python?tabs=get-started%2Casgi%2Capplication-level&pivots=python-mode-decorators

```python
import logging 

import azure.functions as func 

bp = func.Blueprint() 

@bp.route(route="default_template") 
def default_template(req: func.HttpRequest) -> func.HttpResponse: 
    logging.info('Python HTTP trigger function processed a request.') 

    name = req.params.get('name') 
    if not name: 
        try: 
            req_body = req.get_json() 
        except ValueError: 
            pass 
        else: 
            name = req_body.get('name') 

    if name: 
        return func.HttpResponse( 
            f"Hello, {name}. This HTTP-triggered function " 
            f"executed successfully.") 
    else: 
        return func.HttpResponse( 
            "This HTTP-triggered function executed successfully. " 
            "Pass a name in the query string or in the request body for a" 
            " personalized response.", 
            status_code=200 
        )
```

We will only reference the **getNotes** endpoint in this summary as there are further explanations and examples provided from the API reference endpoint. The endpoint is defined with a decorator (@) with a route *get/Notes* with one valid method of GET. Each endpoint will have it's own valid method respectively. It then logs the endpoint action with a message of "Python HTTP trigger function processed a [GET] request." You will have to access to the logs through your_function_app -> Monitoring -> Logs. Basic knowledge of the kusto query language (KQL) is required to view these logs. 

```kql
traces
| where operation_Name == "getNotes"
| take 10
// this will return the latest 10 logs from the traces table
// the message column will contain your log line
```

Then we proceed with ensuring the api key provided matches the one stored in the key vault.

```python
if not validate_api_key(req):
    logging.warning("[-] Unauthorized access attempt detected.")
    return func.HttpResponse("[-] Unauthorized, Invalid or Missing API Key", status_code=401)
```

Following the key validation, the code attempts to extract the *title* and *note_id* parameters. It then attempts to extract the request body and stores it as *req_body*. If *title* was not provided as a parameter, extract it from the request body. The same is done for *note_id*. If the title is equal to ALL, or both *title* and *note_id* are null, the endpoint will return all notes. If a different *title* or *note_id* was provided it will call **query_notes** or **query_notes_id** respectively, else it will return a 404 with a message of "Note not found". If nothing was provided in the JSON body or in parameters it will return a 400 for bad request.

The **getNotes** endpoint is the only endpoint that allows "ALL" as the *title* parameter. 

## Overview

*Refer To MyFunctionProject/requirements.txt For Dependencies*

### API Reference/Usage

*Refer To Reference Link for API Usage*: **https://notesfuncapp111.azurewebsites.net/api/docs**

### Endpoint Overview

This function app supports 5 http methods:

-GET

-POST

-PUT

-DELETE

-PATCH

In function_app.py there are 6 endpoints defined by a python decorator (@), routes are defined as:

-get/notes

-get/notes/count

-post/notes

-put/notes

-delete/notes

-patch/Notes/validateStale

#### Endpoint Purpose

All requests and responses utilizes **JSON**

When sending data in the request body, the content must be JSON

GET request parameters may also be passed directly in the URL as query parameters

Please note that **title**, **category**, **data** are the only inputs that will be processed by the function app in a POST or PUT request. In endpoints like get/Notes, and delete/Notes only **title** is required. In the case of get/Notes it is not necessary to pass any parameters if retrieving all notes is the desired outcome. In any endpoint that accepts a **title** argument, it may also be subsituted with **note_id** if desired (except for __post/Notes__).

##### GET

**Route**: *https://notesfuncapp111.azurewebsites.net/api/get/Notes*

This endpoint retrieves individual or all notes.

GET requests may also be passed as a parameter in your browser of choice

*https://notesfuncapp111.azurewebsites.net/api/get/Notes?code=apikey&title=ALL*

--------------

**Route**: *https://notesfuncapp111.azurewebsites.net/api/get/Notes/count*

The **COUNT** function is also a GET request. It takes no parameters and will return the length (count) of note entries in storage. If parameters are provided they will be ignored. Simply request the url.

API Key is still required and may be passed in the request header as either x-functions-key or code. Or it may be passed in the url like below.

*https://notesfuncapp111.azurewebsites.net/api/get/Notes/count?code=apikey*

##### POST

**Route**: *https://notesfuncapp111.azurewebsites.net/api/post/Notes*

This endpoint creates individual notes and stores it as an entity in azure table storage. **note_id** may not be used here as the __row_key__ required by azure table storage is the lower cased title. **note_id** was implemented as a way to give users more options in reading and writing to existing notes.
 
"ALL" is invalid here and will result in a malformed request.

NOTE: **Title** must be unique, duplicate titles will result in a conflict error (STATUS_CODE = 409)

Upon a successful POST the title will not be modifiable, **category** and **data** are the only modifiable parameters.

##### PUT

**Route**: *https://notesfuncapp111.azurewebsites.net/api/put/Notes*

This endpoint updates existing notes. The only modifiable parameters are **category** and **data**. Notes may be referenced with **title** or **note_id**.

"ALL" is invalid here and will result in a malformed request.

##### DELETE

**Route**: *https://notesfuncapp111.azurewebsites.net/api/delete/Notes*

This endpoint deletes existing notes. The only parameter required here is either a **title** or **note_id**.

NOTE: This is an irreversible action, proceed with caution.

"ALL" is invalid here and will result in a malformed request.

##### PATCH

**Route**: *https://notesfuncapp111.azurewebsites.net/api/put/Notes*

This endpoint updates the __isStale__ parameter. It is false by default and after the last modified time has surpassed 5 minutes from __datetime.now()__, this endpoint will mark those notes as stale at next call. No parameters are required here, if any are provided they will not be processed. Users do not have to worry about calling this endpoint as there is a logic app that automates this process periodically (set to every 1 day by at the moment). If desired manually calling this endpoint will have the same effect as the logic app. 

To modify time to stale, refer to line 288 in function_app.py:

```python
stale = datetime.timedelta(minutes=5)
```

## Setup

For this set of instructions, it is assumed that visual studio code is the IDE being utilized. Install extensions:

-Python
-Python Debugger
-Python Environments
-Pylance
-Azure Functions
-Azure Repos
-Azure Resources

In the azure extension, sign in with your Microsoft account.

### Function App

You may utilize the script __deploy.ps1__ to deploy through your terminal. If desired you may also manually create the function app at https://portal.azure.com/.

Deploy code with:

```shell
func azure functionapp publish <function_app_name>
```

### Storage Account

A storage account should have been automatically created upon creation of the function app. For whatever reason if a function app was not created, manually create one in azure and create a table. Give the function app a system assigned managed identity. Give that managed identity "Storage Table Data Contributor". 

### Key Vault

Create a key vault resource. Select a key in the function app and store it as a secret within the function app. Assign the function app managed identity, "Key Vault Reader" and "Key Vaults Secret User".

### Logic App

The logic app code view is provided in __logicapp.json__. Since the code view is already provided, I will only give a high level overview. The logic app is set on a recurrence schedule of every 24 hours to start at 8am. It then uses the built in action of __Get Secrets__. Therefore, the logic app will also require a system assigned managed identity unless you have created an user assigned managed identity. The managed identity must be assigned "Key Vault Reader" and "Key Vault Secrets User". The next action calls the validation endpoint. Then it proceeds into its fork. The fork checks if the status code is equal to 200. If yes it will send an email indicating the run was successful. If not will also send an email but will indicate that the run failed. If copying and pasting the coded view, the emails with ones that you have direct access to. 