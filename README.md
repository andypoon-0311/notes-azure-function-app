# notes-azure-function-app
Simple function app in python to store notes using azure python sdk v2.

**Click Here To Watch a Demo, Will Redirect To Youtube**
<p align="center">
  <a href="https://youtu.be/LMVBpxSYq-s">
    <img src="https://img.youtube.com/vi/LMVBpxSYq-s/0.jpg" alt="Watch the demo" width="70%">
  </a>
</p>

The function app is connected to Azure Table Storage so that data may persist on stable storage rather than living only in memory.

By navigating to MyFunctionProject/function_app.py you will see the first 3 helper functions to facilitate this connection to blob storage.

**get_table_service_client** connects to the storage account using the function app's system assigned managed identity. In the code you may see "STORAGE_ACCOUNT" as the value for the variable **account_name**. "STORAGE_ACCOUNT" is just the name of the environment variable in azure that contains the name of the target storage account, just as if you were using a local .env file to store a key to a resource. It then proceeds to try and get the **table_client**, following that it attempts to create the table and if it already exists it does nothing. The return value is **table_client**.

**query_notes** gets a reference to the table by calling **get_table_service_client**. If no title is passed then it will return all entities. If a title is provided this helper will return the specified entity by using the partition_key "Notes" (Notes is the only partition key that exists in this case) and the row_key (title converted to lower). If nothing is found it will return none.

**query_notes_id** begins similarily to **query_notes**. It attempts to get a reference to the table by calling **get_table_service_client**. Because I have elected to make title the row_key, I must iterate through all entities if I wish to retrieve notes with the **note_id**. The purpose of this helper function is to provide flexibility to the end user in GET operations. Generally the row_key is a numeric value, but in this use case, I thought it would make more sense to retrieve notes by their title, rather than a numeric value that has nothing to do with the contents of the stored note. In any case, users may elect to utilize **note_id** instead of title when attempting to retrieve stored notes.

**create_note** inserts new note entities into Azure Table Storage. It takes three parameters, title (required), category, and data. Title being the only required parameter, the function initializes category and data to None. The function beings by checking for a title value, if one is not provided a Null value will immediately be returned. After this check, a reference is retrieved to the Azure Table Storage resource in a same manner as above. The variable now contains the datetime.now() value in isoformat so that it may be serializable by the function app. The row_key is immediately provided the value of *title.lower()*. 

```python
#overwrite data on line 35
blob_client.upload_blob(json.dumps(data), overwrite=True)
```

The endpoints all follow a similar structure besides **countNotes**. **countNotes** just calls the **read_notes** function and stores it in *notes* as a list of dictionaries (json), and returns the length or number of entries in "notes.json". The structure was obtained from Microsoft's "Developer Reference Guide" and I did not deviate much.

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

We will only reference the **getNotes** endpoint in this summary as there are further explanations and examples below for each endpoint. The endpoint is defined with a decorator (@) with a route *get/Notes* with one valid method of GET. Each endpoint will have it's own valid method respectively. It then logs the endpoint action with a message of "Python HTTP trigger function processed a [GET] request." You will have to access to the logs through your_function_app -> Monitoring -> Logs. Basic knowledge of the kusto query language (KQL) is required to view these logs. 

```kql
traces
| where operation_Name == "getNotes"
| take 10
// this will return the latest 10 logs from the traces table
// the message column will contain your log line
```

Then we proceed to call **read_notes** and store it in the *notes* variable. Following that the code attempts to extract the *title* parameter, if it does not find a *title* parameter it attempts to retrieve the json body and stores it as *req_body*. If both *title* and *req_body* are null, then the function attempts to retrieve the request body and assigns "title" (in the json request body) to *title*. If the title is equal to ALL, the function will return all notes. If a different title was provided the function will attempt to iterate through all notes stored in "notes.json" until it finds the corresponding title, else it will return a 404 with a message of "Note not found". If a title was not provided it will return a status code of 400 for a bad request. 

The **getNotes** endpoint is the only endpoint that allows "ALL" as the *title* parameter. Any nuances in the endpoints will be explained below. 

## Overview

*Refer To MyFunctionProject/requirements.txt for dependencies*

This function app supports 4 http methods:

-GET

-POST

-PUT

-DELETE

In function_app.py there are 5 endpoints defined by a python decorator (@), routes are defined as:

-get/notes

-get/notes/count

-post/notes

-put/notes

-delete/notes

### Structure

All requests and responses utilizes **JSON**

When sending data in the request body, the content must be JSON

GET request parameters may also be passed directly in the URL as query parameters

**Input Format Example**:

```json
{
    "title": "MyNote",
    "category": "General",
    "data": "This is a note"
}
```

**Output Format Example**:

```json
{
    "title": "MyNote",
    "category": "General",
    "data": "This is a note",
    "post_date": "2025-09-22T18:30:00.123456",
    "last_modified_date": "2025-09-22T18:30:00.123456"
}
```

Please note that **post_date** and **last_modified_date** are added to note entries by the API. You should NOT include these parameters in your input.

Attempting to modify these parameters will result in no change as they are not user writable.

### Examples

#### GET

**Route**: *https://notesfuncapp111.azurewebsites.net/api/get/Notes*

The only parameter required is the **title** parameter. Titles must be unique. If title is equal to "ALL", all notes will be returned.

```json
{
    "title": "this is my title"
}
```

GET requests may also be passed as a parameter in your browser of choice

*https://notesfuncapp111.azurewebsites.net/api/get/Notes?code=apikey&title=ALL*

--------------

**Route**: *https://notesfuncapp111.azurewebsites.net/api/get/Notes/count*

The **COUNT** function is also a GET request. It takes no parameters and will return the length (count) of note entries in storage. If parameters are provided they will be ignored. Simply request the url.

API Key is still required and may be passed in the request header as either x-functions-key or code. Or it may be passed in the url like below.

*https://notesfuncapp111.azurewebsites.net/api/get/Notes/count?code=apikey*

#### POST

**Route**: *https://notesfuncapp111.azurewebsites.net/api/post/Notes*

The minimum amount of parameters required for a POST is the **title** parameter. Users may also add **category** and **data**. These values must be passed through the request body and NOT as a query parameter as part of the url. The date parameters are ignored if passed, the function app will handle this for you. "ALL" is invalid here and will result in a malformed request.

NOTE: **Title** must be unique, duplicate titles will result in a malformed request (STATUS_CODE = 400)

```json
{
    "title": "this is my title",
    "category": "General",
    "data": "this is my data"
}
```

Upon a successful POST the title will not be modifiable, **category** and **data** are the only modifiable parameters.

#### PUT

**Route**: *https://notesfuncapp111.azurewebsites.net/api/put/Notes*

The minimum amount of parameters required for a PUT is the **title** parameter. However, by failing to provide **category** and **data** no changes will be made to the note besides the **last_modified** date. "ALL" is invalid here and will result in a malformed request.

```json
{
    "title": "this is my title",
    "category": "change to category",
    "data": "change to data"
}
```

#### DELETE

**Route**: *https://notesfuncapp111.azurewebsites.net/api/delete/Notes*

The only parameter required is the **title** parameter. The corresponding note will be removed from storage. "ALL" is invalid here and will result in a malformed request.

```json
{
    "title": "i want to delete this note"
}
```
