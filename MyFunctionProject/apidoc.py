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
        <style>
            body {
            margin: 0;
            background-color: #121212;
            color: #e0e0e0;
            font-family: Segoe UI, Helvetica, Arial, sans-serif;
            }
            #redoc-container {
            height: 100vh;
            }
        </style>
        </head>
        <body>
        <div id="redoc-container"></div>

        <script src="https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"></script>
        <script>
        Redoc.init('/api/openapi.json', {
        theme: {
            colors: {
            primary: { main: '#00bcd4' },
            text: {
                primary: '#ffffff',
                secondary: '#cccccc'
            },
            http: {
                get: "#03a9f4",
                post: "#4caf50",
                put: "#ff9800",
                delete: "#f44336",
                patch: "#9c27b0"
            },
            border: {
                dark: "#333333",
                light: "#444444"
            }
            },
            typography: {
            fontSize: '15px',
            fontFamily: 'Segoe UI, Helvetica, Arial, sans-serif',
            headings: {
                fontSize: '1.1em',
                fontWeight: 'bold',
                color: '#ffffff'
            },
            code: {
                backgroundColor: "#1e1e1e",
                color: "#00e5ff"
            }
            },
            sidebar: {
            backgroundColor: '#1e1e1e',
            textColor: '#e0e0e0'
            },
            rightPanel: {
            backgroundColor: "#1a1a1a",
            textColor: "#e0e0e0"
            },
            schema: {
            labelsTextColor: "#e0e0e0",  
            requireLabelColor: "#ff4081",
            typeNameColor: "#00bcd4",
            nestedBackground: "#1f1f1f"
            }
        }
        }, document.getElementById('redoc-container'));
        </script>
        </body>
        </html>

    """
    return func.HttpResponse(html, mimetype="text/html")
