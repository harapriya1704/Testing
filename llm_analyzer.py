import os
import json
from openai import OpenAI
import httpx
import certifi
from dotenv import load_dotenv
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv('.env', override=True)

class LLMAnalyser:
    def __init__(self):
        self.client = self._setup_client()
        self.prompt_template = self._load_prompt_template()
        self.model = "codestral-22b-v0-1"
        self.max_tokens = 400

    def _setup_client(self):
        http_client = httpx.Client(verify=certifi.where())
        return OpenAI(
            base_url='https://genai-api-dev.dell.com/v1',
            http_client=http_client,
            api_key=os.environ["DEV_GENAI_API_KEY"]
        )

    def _load_prompt_template(self):
        return """**DSAT Root Cause Analysis**

**Data Sources**:
{feedback_section}
2. Behavioral Insights (GIA): {gia_insights}
3. Client-Side Sessions: {client_sessions}
4. Server-Side Errors: {server_sessions}
5. Order Details: {order_details}

**Analysis Instructions**:
1. If customer feedback is provided, perform sentiment analysis.
2. Compare the feedback with technical evidence from client/server sessions and order details.
3. If the feedback clearly matches a technical problem, use that as the PRIMARY cause.
4. If no match is found, identify the PRIMARY cause from: [client-side, server-side, shipping delay, delivery delay, missing carrier link, waybill email failure, payment issue, technical error]
5. Only classify as 'Technical Error' if the issue is backend-related or spans multiple layers.
6. For server-side issues: Extract page name from URL.
7. For client-side issues: Note specific struggles from GIA.
8. Match customer comments to technical evidence wherever possible.
9. If multiple causes are evident, list all relevant.

**Output Format**:
Reason: <comma-separated causes>
Details: <2-line summary with specific page names if server-side>
"""

    def _extract_page_names(self, server_sessions):
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
        try:
            server_pages = self._extract_page_names(context.get("Server-Sessions", ""))
            improve_text = context.get("improve_text", "").strip().lower()

            # Define placeholder values
            placeholder_values = {
                "no", "null", "none", "no comment", "no comments",
                "n/a", "na", "nan", "none provided", "not available", "not applicable"
            }

            # Determine feedback section
            if improve_text and improve_text not in placeholder_values:
                feedback_section = f"1. Customer Feedback: {improve_text}"
            else:
                feedback_section = "1. Customer Feedback: No comment was provided by the customer."

            formatted_prompt = self.prompt_template.format(
                feedback_section=feedback_section,
                gia_insights=context.get("gia_insights", "N/A"),
                client_sessions=context.get("Client-Sessions", "N/A"),
                server_sessions=f"{context.get('Server-Sessions', 'N/A')}\nPages: {server_pages}",
                order_details=json.dumps(context.get("order_details", {}), indent=2)
            )

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
