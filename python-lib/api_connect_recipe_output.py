from contextlib import ExitStack
from datetime import date, datetime
from numbers import Integral, Real

import numpy as np
import pandas as pd
from dataiku.core.schema_handling import get_schema_from_df

from api_connect_dku_constants import DKUConstants


def value_kind(value):
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (bool, np.bool_)):
        return "boolean"
    if isinstance(value, Integral):
        return "integer"
    if isinstance(value, Real):
        return "number"
    if isinstance(value, (datetime, date)):
        return "date"
    if isinstance(value, (str, bytes)):
        return "string"
    return type(value).__name__


def write_streamed_pages(dataset, pages, is_raw_output, unique_schema, batch_size=1000):
    if batch_size <= 0:
        raise ValueError("Batch size must be positive")
    schema = None
    column_kinds = {}
    pending_empty_rows = 0
    with ExitStack() as stack:
        for page in pages:
            if not page:
                continue
            if schema is None:
                dataframe = pd.DataFrame(page)
                if dataframe.size == 0:
                    pending_empty_rows += len(page)
                    continue
                schema = get_schema_from_df(dataframe)
                for column in schema:
                    name = column["name"]
                    column_kinds[name] = {value_kind(row.get(name)) for row in page} - {None}
                    if column["type"] in ("float", "double"):
                        column_kinds[name] = {"integer", "number"}
                    elif not column_kinds[name]:
                        column_kinds[name] = {"string"}
                if is_raw_output and DKUConstants.API_RESPONSE_KEY not in dataframe.columns:
                    schema.append({"name": DKUConstants.API_RESPONSE_KEY, "type": "string"})
                    column_kinds[DKUConstants.API_RESPONSE_KEY] = {"string"}
                if DKUConstants.REPONSE_ERROR_KEY not in dataframe.columns:
                    schema.append({"name": DKUConstants.REPONSE_ERROR_KEY, "type": "string"})
                else:
                    for column in schema:
                        if column["name"] == DKUConstants.REPONSE_ERROR_KEY:
                            column["type"] = "string"
                column_kinds[DKUConstants.REPONSE_ERROR_KEY] = {"string"}
                dataset.write_schema(schema)
                writer = stack.enter_context(dataset.get_writer())
                del dataframe
            columns = [column["name"] for column in schema]
            while pending_empty_rows:
                count = min(pending_empty_rows, batch_size)
                writer.write_dataframe(pd.DataFrame(index=range(count), columns=columns))
                pending_empty_rows -= count
            for offset in range(0, len(page), batch_size):
                rows = []
                for row in page[offset:offset + batch_size]:
                    output_row = {}
                    errors = []
                    for name, value in row.items():
                        if name not in column_kinds:
                            errors.append("unexpected column '{}'".format(name))
                        elif unique_schema and value_kind(value) is not None and value_kind(value) not in column_kinds[name]:
                            errors.append("incompatible type for column '{}' (expected {}, got {})".format(
                                name, "/".join(sorted(column_kinds[name])), value_kind(value)
                            ))
                        else:
                            output_row[name] = value
                    if errors:
                        error = "Response schema changed: {}".format("; ".join(errors))
                        existing_error = row.get(DKUConstants.REPONSE_ERROR_KEY)
                        if existing_error:
                            error = "{}; {}".format(existing_error, error)
                        output_row[DKUConstants.REPONSE_ERROR_KEY] = error
                    rows.append(output_row)
                dataframe = pd.DataFrame(rows, columns=columns)
                for column in schema:
                    name = column["name"]
                    if column["type"] in ("float", "double"):
                        dataframe[name] = pd.to_numeric(dataframe[name]).astype(float)
                    elif column["type"] in ("int", "bigint"):
                        dataframe[name] = dataframe[name].astype("Int64")
                writer.write_dataframe(dataframe)
                del dataframe, rows
