# Cobuild guidance

Use this recipe to call a REST API once for each row of the input dataset and write the extracted response to the output dataset.

Roles:
- `input_A_role`: required input dataset containing the variables used in URL, header, query, body, and pagination templates.
- `api_output`: required output dataset for the API response rows.

Core configuration:
- Set `endpoint_url` to the URL template. Dataset columns can be referenced as `{{column_name}}`.
- Set `http_method` to `GET`, `POST`, `PUT`, `PATCH`, or `DELETE`.
- Use `endpoint_query_string` for query parameters and `endpoint_headers` for headers.
- Use `parameter_columns` to expose input columns as template variables.
- Use `parameter_renamings` when column names should map to cleaner template variable names.
- Use `body_format`, `text_body`, or `key_value_body` for request bodies. `text_body` is visible for `RAW`; `key_value_body` is visible for `FORM_DATA` and `MULTIPART_FORM_DATA`.
- Set `extraction_key` when the response data is nested under a JSON key. Keep `raw_output=true` when the full response JSON should be kept.

Authentication and presets:
- This recipe uses preset fields for credentials. Prefer an existing usable preset from the recipe definition.
- For the generic credential preset, keep `auth_type` null and set `credential` to the selected preset name from parameter set `credential`.
- For secure OAuth, set `auth_type=secure_oauth` and set `secure_oauth` to a preset from parameter set `secure-oauth`.
- For secure OAuth with refresh-token rotation, set `auth_type=secure_oauth_refresh_token_rotation` and set `secure_oauth_refresh_token_rotation` to a preset from parameter set `secure-oauth-refresh-token-rotation`.
- For secure basic auth, set `auth_type=secure_basic` and set `secure_basic` to a preset from parameter set `secure-basic`.
- Do not ask the user to paste preset secrets in chat. If no usable preset is available or selected, create the recipe skeleton, navigate to the recipe settings, and ask the user to select or create the preset there.

Pagination:
- Keep `pagination_type=na` unless the API documentation requires pagination.
- For next-page pagination, set `next_page_url_key`, and set `is_next_page_url_relative` plus `next_page_url_base` when the returned next URL is relative.
- For offset or page pagination, set the visible key fields and define `extraction_key` when required by the API response shape.
