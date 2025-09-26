import azure.functions as func
from azure.storage.blob import BlobServiceClient
import logging
import datetime
import os
import json
# establish the connection with the blob
###############################################################################################################
conn_str = os.getenv("AzureWebJobsStorage")             #stored as an environment variable in the azure, azure should do this for you when creating a function app; if receiving an internal server error please check this environment variable in azure
CONTAINER_NAME = "storenotes"
BLOB_NAME = "notes.json"

def get_blob_service_client():
    return BlobServiceClient.from_connection_string(conn_str)

def read_notes():
    client = get_blob_service_client()
    container_client = client.get_container_client(CONTAINER_NAME)
    try:
        container_client.create_container()
    except Exception:
        pass                                            # if the container already exists pass

    blob_client = container_client.get_blob_client(BLOB_NAME)
    try:
        data = json.loads(blob_client.download_blob().readall())
    except Exception:
        data = []
    return data

def save_notes(data):
    client = get_blob_service_client()
    container_client = client.get_container_client(CONTAINER_NAME)
    blob_client = container_client.get_blob_client(BLOB_NAME)
    blob_client.upload_blob(json.dumps(data), overwrite=True)
############################################################################################################################

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# POST notes
@app.route(route="post/Notes", methods=["POST"])
def postNotes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a [POST] request.')
    
    notes = read_notes()
    data = None
    #title = None

    title = req.params.get("title")
    try:
        req_body = req.get_json()
    except ValueError:
        req_body = {}

    if not title and not req_body:
        title = req_body.get("title")
    if title and title != "ALL":
        data = {
            "title": title,
            "category": req_body.get("category"),
            "data": req_body.get("data"),
            "post_date": datetime.datetime.now().isoformat(),
            "last_modified_date": datetime.datetime.now().isoformat()
        }
    is_duplicate = any(n for n in notes if n["title"].lower() == title.lower()) if title else False
    if data and title and not is_duplicate:
        notes.append(data)
        save_notes(notes)
        return func.HttpResponse(f"[+] [POST] request successful\n{data}\n", status_code=201)
    else:
        return func.HttpResponse(
            "[-] Bad [POST] request.\n Title is required, category and data optional.\n ALL is invalid.\nDuplicate titles are not allowed.",
            status_code=400
        )

# GET notes
@app.route(route="get/Notes", methods=["GET"])
def getNotes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a [GET] request.')
    notes = read_notes()

    title = req.params.get("title")
    try:
        req_body = req.get_json()
    except ValueError:
        req_body = {}

    if not title and req_body:
        title = req_body.get("title")

    if title == "ALL":
        return func.HttpResponse(json.dumps(notes), mimetype="application/json", status_code=200)
    elif title:
        note = next((n for n in notes if n["title"].lower() == title.lower()), None)
        if note:
            return func.HttpResponse(json.dumps(note), mimetype="application/json", status_code=200)
        else:
            return func.HttpResponse("[-] Note not found.", status_code=404)
    else:
        return func.HttpResponse(
            "[-] Bad [GET] request.\n Provide a title or use title=ALL.",
            status_code=400
        )
    
# PUT notes
@app.route(route="put/Notes", methods=["PUT"])
def putNotes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a [PUT] request.')
    notes = read_notes()

    title = req.params.get("title")
    try:
        req_body = req.get_json()
    except ValueError:
        req_body = {}

    if not title:
        title = req_body.get("title")

    if title == "ALL":
        return func.HttpResponse("[-] ALL is not valid for update.", status_code=400)
    elif title:
        note = next((n for n in notes if n["title"].lower() == title.lower()), None)
        if note:
            for k in ["category", "data"]:
                if k in req_body:
                    note[k] = req_body[k]
            note["last_modified_date"] = datetime.datetime.now().isoformat()
            save_notes(notes)
            return func.HttpResponse(f"[+] PUT successful: {note}", mimetype="application/json", status_code=200)
        else:
            return func.HttpResponse("[-] Note not found.", status_code=404)
    else:
        return func.HttpResponse(
            "[-] Bad [PUT] request.\n Provide a valid title to update.\n ALL is invalid.",
            status_code=400
        )

# DELETE notes
@app.route(route="delete/Notes", methods=["DELETE"])
def deleteNotes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a [DELETE] request.')
    notes = read_notes()

    title = req.params.get("title")
    try:
        req_body = req.get_json()
    except ValueError:
        req_body = {}

    if not title and req_body:
        title = req_body.get("title")

    if title == "ALL":
        return func.HttpResponse("[-] ALL is not valid for deletion.", status_code=400)
    elif title:
        note = next((n for n in notes if n["title"].lower() == title.lower()), None)
        if note:
            deleted = notes.pop(notes.index(note))
            save_notes(notes)
            return func.HttpResponse(f"[+] DELETE successful: {deleted}", mimetype="application/json", status_code=200)
        else:
            return func.HttpResponse("[-] Note not found.", status_code=404)
    else:
        return func.HttpResponse(
            "[-] Bad [DELETE] request.\n Provide a valid title to delete.\n ALL is invalid.",
            status_code=400
        )

# GET notes count
#this takes not parameters and will ignore all parameters if provided will only return the length (count) of notes
@app.route(route="get/Notes/count", methods=["GET"])
def countNotes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a [GET] request.')
    notes = read_notes()
    return func.HttpResponse(json.dumps({"count": len(notes)}), mimetype="application/json", status_code=200)
