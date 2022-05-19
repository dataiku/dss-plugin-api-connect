# Changelog


## [Version 1.0.6](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.0.6) - Feature and bugfix release - 2022-05-19

- Add "Follow authorization header" option
- Fix for RFC5988 pagination

## [Version 1.0.5](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.0.5) - Bugfix release - 2022-03-30

- Fix use of "Next page pagination" with short extraction path

## [Version 1.0.4](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.0.4) - Bugfix release - 2021-12-14

- Fix use of "Next page pagination" in combination with extraction path
- Extraction path added to recipe

## [Version 1.0.3](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.0.3) - Bugfix and feature release - 2021-11-23

- Fixes error raised on HTTP 204 status codes
- Adds requests performance indicator to output datasets
- Data extraction key is replaced by a path
- Fixes JSON formatting issues
- Implements RFC5988 for pagination

## [Version 1.0.2](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.0.2) - Bugfix release - 2021-05-25

- Fixed recipe ignoring the selected http_method

## [Version 1.0.1](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.0.1) - Bugfix release - 2021-05-03

- Fixed the "Per page" pagination mode

## [Version 1.0.0](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.0.0) - Initial release - 2021-04-14

- Initial release
- Retrieve data from 3rd party API by describing URL, headers, query parameters and authentication with templates
- Custom Dataset for simple data retrievals
- Custom Recipe using an input dataset as variables for your templates
- Implements basic authentication, bearer token, API key
