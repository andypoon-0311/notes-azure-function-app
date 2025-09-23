# notes-azure-function-app
Simple function app in python to store notes using azure python sdk v2

Disclaimer: For anyone else that may come across this repository, this was for a school project, please excuse the sloppy code if it comes off as sloppy I am not a developer by trade. And if you wish, feel free to take it and make it better for your own purpose.

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
