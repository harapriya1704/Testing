import os
import json
from openai import OpenAI
import httpx
import certifi
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv('.env', override=True)

class LLMAnalyser:
    def __init__(self):
        self.client = self._setup_client()
        self.prompt_template = self._load_prompt_template()
        self.model = "mixtral-8x7b-instruct-v01"
        self.max_tokens = 300

    def _setup_client(self):
        """Set up authenticated API client"""
        http_client = httpx.Client(verify=certifi.where())
        return OpenAI(
            base_url='https://genai-api-dev.dell.com/v1',
            http_client=http_client,
            api_key=os.environ["DEV_GENAI_API_KEY"]
        )

    # In llm_analyser.py
    def _load_prompt_template(self):
        return """**DSAT Root Cause Analysis**

    **Data Sources**:
    1. Customer Feedback: {improve_text}
    2. Behavioral Insights (GIA): {gia_insights}
    3. Client-Side Sessions: {client_sessions}
    4. Server-Side Errors: {server_sessions}
    5. Order Details: {order_details}

    **Analysis Instructions**:
    1. Identify PRIMARY cause from: [client-side, server-side, shipping delay, delivery delay, missing carrier link, waybill email failure, payment issue, technical error]
    2. For server-side issues: Extract page name from URL
    3. For client-side issues: Note specific struggles from GIA
    4. Match customer comments to technical evidence
    5. If multiple causes: List all relevant

    **Output Format**:
    Reason: <comma-separated causes>
    Details: <2-line summary with specific page names if server-side>
    """

    def _extract_page_names(self, server_sessions):
        """Extract page names from server session URLs"""
        if "No error sessions found" in server_sessions:
            return "No server errors"
            
        pages = set()
        for line in server_sessions.split('\n'):
            if 'URL:' in line:
                url = line.split('URL: ')[1].strip()
                path = urlparse(url).path
                if '/' in path:
                    page = path.split('/')[-1] or path.split('/')[-2]
                    pages.add(page)
        return ", ".join(pages) if pages else "No identifiable pages"

    def analyze_dsat(self, context):
        """Analyze DSAT using all available data"""
        try:
            # Preprocess server sessions
            server_pages = self._extract_page_names(context["Server-Sessions"])
            
            # Prepare prompt
            formatted_prompt = self.prompt_template.format(
                gia_insights=context.get("gia_insights", "N/A"),
                client_sessions=context.get("Client-Sessions", "N/A"),
                server_sessions=f"{context.get('Server-Sessions', 'N/A')}\nPages: {server_pages}",
                order_details=json.dumps(context.get("order_details", {}), indent=2),
                improve_text=context.get("improve_text", "N/A")
            )
            
            # Call LLM API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a customer experience analyst"},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.3,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            return "Reason: analysis error\nDetails: Failed to generate summary"
