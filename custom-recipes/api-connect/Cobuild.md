# Cobuild guidance

Role-specific behavior:
- `input_A_role` supplies one API call per row and the column values available to request templates.
- `api_output` collects the response rows extracted from those calls and any paginated responses.

Request behavior:
- Columns selected in `parameter_columns` become `{{column_name}}` template variables across the URL, headers, query parameters, body, and pagination settings; `parameter_renamings` changes their template names.
- `should_use_user_secrets=true` also exposes the current user's Profile > My account > Other credentials as template variables.
- `body_format=RAW` uses `text_body`; `FORM_DATA` and `MULTIPART_FORM_DATA` use `key_value_body`.
- `auth_type=null` selects the generic `credential` preset path; each secure authentication type selects its corresponding preset field.

Response extraction:
- Use the dot-separated `extraction_key` when response rows are nested under a JSON path.
- Keep `raw_output=true` when each response item should be preserved as raw JSON instead of flattened into columns.

Pagination:
- Select the pagination mechanism from the target API's documentation; do not infer one from the endpoint shape.
- For next-page pagination, `next_page_url_key` is the dot-separated response path containing the following request URL. When that URL is relative, enable `is_next_page_url_relative` and provide `next_page_url_base`.
- Page pagination requires `extraction_key` so the recipe can locate and count the returned data array.
- For offset and page pagination, `skip_key` is the query parameter carrying the next offset or page number.
