# Copyright 2023 Google LLC
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


from typing import Any, List

import sqlparse


class UIFriendlyLogger:
    friendly_log: str = ""

    def log(self, message: str):
        self.friendly_log += f"{message}<br/>"

    def log_error(self, message: str):
        self.friendly_log += f'<div class="error">{message}</div><br/>'

    def log_section_header(self, message: str):
        self.friendly_log += f'<div class="header">{message}</div>'

    def log_header(self, message: str):
        self.friendly_log += f"<br><b>{message}</b><br/>"

    def log_code(self, message: str):
        self.friendly_log += f'<div class="codeblock">{message}</div>'

    def log_results(self, results: List[Any]):
        self.friendly_log += (
            f'<div class="results">{"<br>".join(map(str, results))}</div>'
        )

    def log_list_string_as_result(self, header: str, results: List[str]):
        html = f"<table border='1'><tr><th>{header}</th></tr>"
        for row in results:
            html += f"<tr><td>{row}</td></tr>"
        html += "</table>"
        self.log_results([html])

    def log_list_dict_as_result(self, results: List[dict]):
        if not results:
            self.log_results(["There are no results to show."])
            return
        try:
            html = "<table border='1'><tr>"
            for key in results[0].keys():
                html += f"<th>{key}</th>"
            html += "</tr>"
            for row in results:
                html += "<tr>"
                for key in results[0].keys():
                    html += f"<td>{row.get(key, '')}</td>"
                html += "</tr>"
            html += "</table>"
            self.log_results([html])
        except Exception as e:
            self.log_results([str(results)])

    def log_SQL(self, sql: str, params):
        # replace each $i with the params
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
        self.log_code(formatted_sql.replace("<br/>", "", 1))

    def get_log(self):
        return f'<div class="actionblock">{self.friendly_log}</div>'
