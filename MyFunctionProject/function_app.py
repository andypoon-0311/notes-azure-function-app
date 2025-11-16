import azure.functions as func
from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from apidoc import bp
import logging
import datetime
import os
import json

STORAGE_ACCOUNT = "STORAGE_ACCOUNT"
TABLE_NAME = "NotesTable"

def get_table_service_client():
    account_name = os.getenv(STORAGE_ACCOUNT)
    credential = DefaultAzureCredential()
    service = TableServiceClient(endpoint=f"https://{account_name}.table.core.windows.net", credential=credential)
    table_client = service.get_table_client(TABLE_NAME)

    try:
        table_client.create_table()
    except:
        pass

    return table_client

def query_notes(title=None):
    table = get_table_service_client()
    if title is None:
        return list(table.list_entities())
    try:
        entity = table.get_entity(partition_key="Notes", row_key=title.lower())
        return entity
    except:
        return None

def query_notes_id(note_id):
    table = get_table_service_client()
    entity = table.list_entities()
    for i in entity:
        if str(i.get("note_id")) == str(note_id):
            return i
    return None

def create_note(title, category=None, data=None):
    if not title:
        return None  #Must have a title to create notes
    
    table = get_table_service_client()
    now = datetime.datetime.now().isoformat()
    row_key = title.lower()

    try:
        already_exists = table.get_entity(partition_key="Notes", row_key=row_key)
        if already_exists:
            return "exists" #In situations where the note already exists according to the row key (title must be unique)
    except:
        pass        #entity in azure table does not exist so we can proceed

    entity = list(table.list_entities())
    if not entity:
        next_id = 1
    else:
        next_id = max(int(i.get("note_id", 0)) for i in entity) + 1 #gets max entity numeric id and adds 1 for a unique id

    entity = {
        "PartitionKey": "Notes",
        "RowKey": row_key,
        "note_id": next_id,
        "title": title,
        "category": category,
        "data": data,
        "post_date": now,
        "last_modified_date": now,
        "isStale": False
    }

    table.create_entity(entity=entity)
    return entity
 
def get_api_key():
    key_vault_url = os.getenv("KEY_VAULT_URL") 
    secret_name = "funcApp-apiKey"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=key_vault_url, credential=credential)
    secret = client.get_secret(secret_name)
    return secret.value

def validate_api_key(req: func.HttpRequest):
    incoming = req.headers.get("x-functions-key")
    if not incoming:
        return False
    
    expected = get_api_key()
    return incoming == expected

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
app.register_functions(bp)

# POST notes
@app.route(route="post/Notes", methods=["POST"])
def postNotes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a [POST] request.')

    if not validate_api_key(req):
        logging.warning("[-] Unauthorized access attempt detected.")
        return func.HttpResponse("[-] Unauthorized, Invalid or Missing API Key.", status_code=401)
    
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("[-] Bad [POST] request. Invalid JSON.", status_code=400)

    title = req_body.get("title")
    category = req_body.get("category")
    data = req_body.get("data")
    
    if not title or title == "ALL":
        return func.HttpResponse("[-] Bad [POST] request.\n Title is required and ALL is invalid.", status_code=400)
    
    entity = create_note(title, category, data)
    if entity == "exists":
        return func.HttpResponse("[-] Note with this title already exists.", status_code=409)  #Conflict
    
    return func.HttpResponse(json.dumps({"[+] POST successful": entity}), mimetype="application/json", status_code=201)

# GET notes
@app.route(route="get/Notes", methods=["GET"])
def getNotes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a [GET] request.')

    if not validate_api_key(req):
        logging.warning("[-] Unauthorized access attempt detected.")
        return func.HttpResponse("[-] Unauthorized, Invalid or Missing API Key.", status_code=401)

    title = req.params.get("title")
    note_id = req.params.get("note_id")

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("[-] Bad [GET] request. Invalid JSON.", status_code=400)

    if not title and "title" in req_body:
        title = req_body.get("title")
    
    if not note_id and "note_id" in req_body:
        note_id = req_body.get("note_id")

    if title == "ALL" or (title is None and note_id is None):   #If no title or note_id provided, or title is ALL, get all notes
        entity = query_notes
        return func.HttpResponse(json.dumps(entity()), mimetype="application/json", status_code=200)
    
    if note_id:
        entity = query_notes_id(note_id)
        if entity is None:
            return func.HttpResponse("[-] Note not found.", status_code=404)
        return func.HttpResponse(json.dumps(entity), mimetype="application/json", status_code=200)

    if title:
        entity = query_notes(title)
        if entity is None:
            return func.HttpResponse("[-] Note not found.", status_code=404)
        return func.HttpResponse(json.dumps(entity), mimetype="application/json", status_code=200)
    
    return func.HttpResponse("[-] Bad [GET] request.\n Provide a valid title or note_id to retrieve note.", status_code=400)

# PUT notes
@app.route(route="put/Notes", methods=["PUT"])
def putNotes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a [PUT] request.')

    if not validate_api_key(req):
        logging.warning("[-] Unauthorized access attempt detected.")
        return func.HttpResponse("[-] Unauthorized, Invalid or Missing API Key.", status_code=401)

    title = req.params.get("title")
    note_id = req.params.get("note_id")
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("[-] Bad [PUT] request. Invalid JSON.", status_code=400)

    if "title" in req_body and not title:
        title = req_body.get("title")
    if "note_id" in req_body and not note_id:
        note_id = req_body.get("note_id")

    if title == "ALL":
        return func.HttpResponse("[-] ALL is not valid for update.", status_code=400)
    if note_id:
        entity = query_notes_id(note_id)
        if entity is None:
            return func.HttpResponse("[-] Note not found.", status_code=404)
    elif title:
        entity = query_notes(title)
        if entity is None:
            return func.HttpResponse("[-] Note not found.", status_code=404)
    else:
        return func.HttpResponse("[-] Bad [PUT] request.\n Provide a valid title or note_id to update note.\n ALL is invalid.", status_code=400)

    updated = False
    for i in ["category", "data"]:
        if i in req_body:
            entity[i] = req_body[i]
            updated = True
    
    if not updated:
        return func.HttpResponse("[-] No valid fields to update provided.", status_code=400)
    
    entity["last_modified_date"] = datetime.datetime.now().isoformat()
    table = get_table_service_client()
    table.update_entity(entity=entity, mode="replace")

    return func.HttpResponse(json.dumps({"[+] PUT (Update) Successful For": entity}), mimetype="application/json", status_code=200)

# DELETE notes
@app.route(route="delete/Notes", methods=["DELETE"])
def deleteNotes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a [DELETE] request.')

    if not validate_api_key(req):
        logging.warning("[-] Unauthorized access attempt detected.")
        return func.HttpResponse("[-] Unauthorized, Invalid or Missing API Key.", status_code=401)

    title = req.params.get("title")
    note_id = req.params.get("note_id")
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse("[-] Bad [DELETE] request. Invalid JSON.", status_code=400)

    if not title and "title" in req_body:
        title = req_body.get("title")
    if not note_id and "note_id" in req_body:
        note_id = req_body.get("note_id")

    if title == "ALL":
        return func.HttpResponse("[-] ALL is not valid for deletion.", status_code=400)

    table = get_table_service_client()

    if note_id:
        entity = query_notes_id(note_id)
        if entity is None:
            return func.HttpResponse("[-] Note not found.", status_code=404)
        
        table.delete_entity(partition_key="Notes", row_key=entity["RowKey"])
        return func.HttpResponse(json.dumps({"[+] DELETE successful for": entity}), status_code=200)
    
    if title:
        entity = query_notes(title)
        if entity is None:
            return func.HttpResponse("[-] Note not found.", status_code=404)
        
        table.delete_entity(partition_key="Notes", row_key=entity["RowKey"])
        return func.HttpResponse(json.dumps({"[+] DELETE successful for title": entity}), status_code=200)
    
    return func.HttpResponse("[-] Bad [DELETE] request.\n Provide a valid title or note_id to delete note.\n ALL is invalid.", status_code=400)

# GET notes count
#this takes not parameters and will ignore all parameters if provided will only return the length (count) of notes
@app.route(route="get/Notes/count", methods=["GET"])
def countNotes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a [GET] request.')

    if not validate_api_key(req):
        logging.warning("[-] Unauthorized access attempt detected.")
        return func.HttpResponse("[-] Unauthorized, Invalid or Missing API Key.", status_code=401)

    entity = query_notes()

    count = len(entity)
    return func.HttpResponse(json.dumps({"count": count}), mimetype="application/json", status_code=200)

#PATCH notes to mark as stale
@app.route(route="patch/Notes/validateStale", methods=["PATCH"])
def validateNotes(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a [PATCH] request.')

    if not validate_api_key(req):
        logging.warning("[-] Unauthorized access attempt detected.")
        return func.HttpResponse("[-] Unauthorized, Invalid or Missing API Key.", status_code=401)
    
    table = get_table_service_client()
    notes = query_notes()
    now = datetime.datetime.now()
    stale = datetime.timedelta(minutes=5)  #Stale After 5 minutes (For Demonstration Purposes)
    count = 0

    for i in notes:
        try:
            last_modified = datetime.datetime.fromisoformat(i["last_modified_date"])
        except Exception:
            continue

        if last_modified.tzinfo is not None:
            last_modified = last_modified.replace(tzinfo=None)

        if now - last_modified > stale:
            i["isStale"] = True
            table.update_entity(entity=i, mode="replace")
            count += 1

    response = {
        "updatedCount": count,
        "timestamp": now.isoformat()
    }

    return func.HttpResponse(json.dumps(response), mimetype="application/json", status_code=200)