# Changelog

## [Version 1.2.1](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.2.1) - Feature release - 2023-11-20

- Add secure username / password preset

## [Version 1.2.0](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.2.0) - Feature and bugfix release - 2023-05-31

- Add Brotli compression
- Faster recurring calls
- dku_error column kept at all time in API-Connect recipe output schema
- Updated code-env descriptor for DSS 12

## [Version 1.1.4](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.1.4) - Feature and bugfix release - 2023-02-28

- Add Brotli compression
- Faster recurring calls
- dku_error column kept at all time in API-Connect recipe output schema

## [Version 1.1.3](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.1.3) - Bugfix release - 2023-04-18

- Updated code-env descriptor for DSS 12

## [Version 1.1.2](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.1.2) - Bugfix release - 2022-10-19

- Fix for last page of RFC5988 pagination triggering loop condtion
- Fix for RFC5988 pagination taking priority on other modes
- Improved pagination logs
- Improved error message upon receiving non JSON material

## [Version 1.1.1](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.1.1) - Feature release - 2022-09-22

- Handling relative URLs in paginated APIs

## [Version 1.1.0](https://github.com/dataiku/dss-plugin-api-connect/releases/tag/v1.1.0) - Feature and bugfix release - 2022-09-15

- Handling Offset pagination on APIs returning an array
- Fix throttling calculation
- Allow dots in `Key to next request URL`
- Add NTLM authentication

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
