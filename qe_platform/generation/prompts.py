from __future__ import annotations

TEST_GENERATION_PROMPT = """\
You are a senior QE engineer generating automated test cases for an API endpoint.

Endpoint Specification:
- Path: {path}
- Method: {method}
- Summary: {summary}
- Description: {description}
- Parameters: {parameters}
- Request Body: {request_body}
- Responses: {responses}
- Requires Auth: {requires_auth}
- Risk Tier: {risk_tier}
- Risk Score: {risk_score}

Generate {test_count} test cases covering the following types:
1. **happy_path**: Valid input, expect success response
2. **boundary**: Edge values (empty strings, max length, zero, negative numbers, large payloads)
3. **auth_bypass**: Missing or invalid auth tokens/headers
4. **malformed_input**: Invalid JSON, wrong types, missing required fields
5. **negative**: Valid structure but business-logic invalid (e.g., non-existent ID, duplicate create)

Requirements:
- Each test must have a unique, descriptive name
- Include concrete input data (not placeholders)
- Specify exact expected HTTP status codes
- Include meaningful assertions beyond status code
- For auth_bypass tests, omit or corrupt the Authorization header
- For boundary tests, use actual edge values from the parameter constraints

Respond with ONLY a valid JSON object. No markdown, no explanation. Format:
{{"test_cases": [{{"name": "...", "test_type": "happy_path|boundary|auth_bypass|malformed_input|negative", "description": "...", "input_data": {{}}, "expected_status": 200, "assertions": []}}]}}
"""

SELF_HEALING_PROMPT = """\
A Playwright UI test failed because a selector no longer matches any element on the page.

Test Name: {test_name}
Failed Selector: {broken_locator}
Error Message: {error_message}

Current page DOM (trimmed):
```html
{dom_snapshot}
```

Analyze the DOM and suggest the best replacement selector. Prefer:
1. data-testid attributes
2. aria-label or role-based selectors
3. Stable CSS selectors (avoid nth-child, dynamic classes)

Return ONLY the replacement selector string, nothing else.
"""
