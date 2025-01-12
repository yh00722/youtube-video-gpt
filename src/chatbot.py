from openai import OpenAI, AzureOpenAI

class ChatGPT:
    def __init__(self, api_key, model="gpt-3.5-turbo", azure=False, endpoint=None, deployment_id=None, api_version="2023-07-01-preview"):
        """
        Initialize the chat handler with GPT model and API key.
        Supports both OpenAI and Azure OpenAI.

        Parameters:
        - api_key: Your API key for OpenAI or Azure OpenAI.
        - model: The model to use (default is "gpt-3.5-turbo").
        - azure: Set to True to use Azure OpenAI (default is False).
        - endpoint: Required for Azure OpenAI, the API base URL.
        - deployment_id: Required for Azure OpenAI, the deployment ID for the model.
        - api_version: Required for Azure OpenAI, the API version to use.
        """
        if azure:
            if not endpoint or not deployment_id:
                raise ValueError("For Azure OpenAI, 'endpoint' and 'deployment_id' must be provided.")
            self.client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                azure_deployment=deployment_id,
                api_version=api_version
            )
        else:
            self.client = OpenAI(api_key=api_key)

        self.model = model

    def chat(self, messages, transcription=None, summary=None):
        """
        Use OpenAI or Azure OpenAI GPT API to handle chat interactions.

        Parameters:
        - messages: List of message dictionaries with roles ("system", "user", "assistant") and content.
        - transcription: The transcription text to be included in the system prompt (optional).
        - summary: The summary text to be included in the system prompt (optional).
        """
        try:
            system_prompt = "You are a helpful assistant. Use the following transcription and summary to assist in answering the user's questions:\n\n"
            if transcription:
                system_prompt += f"Transcription:\n{transcription}\n\n"
            if summary:
                system_prompt += f"Summary:\n{summary}\n\n"
            system_prompt += "Provide clear and accurate answers based on this information."

            # Prepend system prompt to the messages
            messages = [{"role": "system", "content": system_prompt}] + messages

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,  # Balance between creativity and focus
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error during chat interaction: {str(e)}")
