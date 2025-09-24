# notes-azure-function-app
Simple function app in python to store notes using azure python sdk v2

Disclaimer: For anyone else that may come across this repository, this was for a school project, please excuse the sloppy code if it comes off as sloppy I am not a developer by trade. And if you wish, feel free to take it and make it better for your own purposes.

## Overview

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

The minimum amount of parameters required for a POST is the **title** parameter. Users may also add the **category** and **data** parameters. All other parameters are ignored. "ALL" is invalid here and will result in a malformed request.

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