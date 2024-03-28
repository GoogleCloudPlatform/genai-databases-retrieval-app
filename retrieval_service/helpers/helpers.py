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


class UIFriendlyLogger:
    friendly_log: str = ""

    def log(self, message: str):
        self.friendly_log += f"{message}</br>"

    def log_error(self, message: str):
        self.friendly_log += f'<div class="error">{message}</div></br>'

    def log_section_header(self, message: str):
        self.friendly_log += f'<div class="header">{message}</div>'

    def log_header(self, message: str):
        self.friendly_log += f"<br><b>{message}</b></br>"

    def log_code(self, message: str):
        self.friendly_log += f'<div class="codeblock">{message}</div>'

    def log_results(self, message: str):
        self.friendly_log += f'<div class="results">{message}</div>'

    def log_SQL(self, sql: str, params):
        for i in range(len(params)):
            sql = sql.replace(f"${i+1}", f"'{params[i]}'")
        self.log_code(sql)

    def get_log(self):
        return f'<div class="actionblock">{self.friendly_log}</div>'
