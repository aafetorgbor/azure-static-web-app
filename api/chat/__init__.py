import azure.functions as func
import json
import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # 1. Parse the inbound message from your HTML/JS frontend
        req_body = req.get_json()
        user_message = req_body.get('message')
        
        if not user_message:
            return func.HttpResponse(
                json.dumps({"error": "Missing 'message' parameter"}),
                status_code=400,
                mimetype="application/json"
            )

        # 2. Authenticate to Azure AI Foundry using Entra ID
        # Locally: Uses your 'az login' session.
        # Azure: Automatically uses your Web App's Managed Identity.
        credential = DefaultAzureCredential()
        
        # Pull your project connection string from the App Settings environment variables
        connection_string = os.environ.get("FOUNDRY_PROJECT_CONNECTION_STRING")
        if not connection_string:
            return func.HttpResponse(
                json.dumps({"error": "Backend configuration error: Missing connection string"}),
                status_code=500,
                mimetype="application/json"
            )

        # 3. Create the client connection to your Foundry project
        project_client = AIProjectClient.from_connection_string(
            conn_str=connection_string,
            credential=credential
        )

        # 4. Initialize an OpenAI/Direct client through Foundry to query your model
        openai_client = project_client.get_openai_client()
        
        # Replace 'gpt-4o-mini' with the Deployment Name of the model in your Foundry Hub
        model_deployment_name = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT", "gpt-4o-mini")

        response = openai_client.responses.create(
            model=model_deployment_name,
            input=user_message
        )

        # 5. Extract the AI output text and pass it back to the web browser
        ai_reply = response.choices[0].message.content

        return func.HttpResponse(
            json.dumps({"reply": ai_reply}),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
