# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sqlparse


def format_sql(sql: str, params):
    """
    Format postgres sql to human readable text
    """
    for i in range(len(params)):
        sql = sql.replace(f"${i+1}", f"{params[i]}")
        # format the SQL
        formatted_sql = (
            sqlparse.format(
                sql,
                reindent=True,
                keyword_case="upper",
                use_space_around_operators=True,
                strip_whitespace=True,
            )
            .replace("\n", "<br/>")
            .replace("  ", '<div class="indent"></div>')
        )
    return formatted_sql.replace("<br/>", "", 1)
