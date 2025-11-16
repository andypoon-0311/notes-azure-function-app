import logging
import os
import azure.functions as func

bp = func.Blueprint()

@bp.route(route="openapi.json", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def openapi(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger for openapi.json.')
    try:
        with open(os.path.join(os.getcwd(), "openapi.json"), "r") as f:
            content = f.read()
        return func.HttpResponse(content, mimetype="application/json", status_code=200)
    except Exception as e:
        logging.error(f"Unable to load OpenApi file: {e}")
        return func.HttpResponse("OpenAPI file not found", status_code=500)

@bp.route(route="docs", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def docs(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger for API documentation.')
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Notes API Documentation</title>
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.css">
    </head>
    <body>
      <redoc spec-url="/api/openapi.json"></redoc>
      <script src="https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    return func.HttpResponse(html, mimetype="text/html")
