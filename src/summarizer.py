from openai import OpenAI, AzureOpenAI

class TextSummarizer:
    def __init__(self, api_key, model="gpt-3.5-turbo", azure=False, endpoint=None, deployment_id=None, api_version="2023-07-01-preview"):
        """
        Initialize the summarizer with the specified GPT model and API key.
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

    def summarize(self, text, user_prompt=None, detected_language=None):
        """
        Use OpenAI or Azure OpenAI GPT API to summarize the given text.
        """
        try:
            default_system_prompt = """You are a professional text summarization and analysis assistant. Your task is to generate a structured summary, provide detailed analysis, and extract key information from the given text. It is critical that your output is in the same language as the original transcription. Present the results in a well-formatted Markdown structure.

            Output Structure:
            1. **Key Points Overview**
            - Summarize the main points in 2-3 sentences.
            - Highlight the central ideas and themes.

            2. **Detailed Section Analysis**
            - Provide a structured breakdown of the text, section by section.
            - Use subheadings for each logical or chronological section.
            - Include important quotes or data points from the original text.
            - Maintain the original tone and style.

            3. **Extracted Keywords**
            - List the top 5-10 most relevant keywords or phrases from the text.
            - Prioritize terms that capture the essence of the content.

            4. **Main Conclusions**
            - Summarize the core viewpoints and important conclusions.
            - Highlight any significant insights or takeaways.

            **Guidelines:**
            - Use the same language as the given text.
            - Ensure accuracy in summarization and analysis.
            - Avoid adding personal opinions or interpretations.
            - Use Markdown syntax for headings, lists, and formatting.
            - Maintain an objective and neutral tone."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": user_prompt or default_system_prompt},
                    {"role": "user", "content": f"Please use {detected_language} to output:\n\n{text}"}
                ],
                temperature=0.8,  # Balance between creativity and consistency
            )

            summary = response.choices[0].message.content
            return summary
        except Exception as e:
            raise Exception(f"Error while summarizing text: {str(e)}")
