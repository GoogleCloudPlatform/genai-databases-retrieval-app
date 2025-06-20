/**
 * Copyright 2024 Google, LLC
 *
 * Licensed under the Apache License, Version 2.0 (the `License`);
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an `AS IS` BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// Create tracing from tool call informations
export function create_trace(toolcalls) {
    let trace = '';
    const toolcalls_len = toolcalls.length;
    for (let i=0; i < toolcalls_len; i++) {
        let toolcall = toolcalls[i];
        trace += trace_section_title(toolcall.tool_call_id);

            trace += trace_header("SQL Executed:");
            trace += trace_sql(toolcall.sql);
        trace += trace_header("Results:");
        trace += trace_results(toolcall.results);

        if (i < toolcalls_len-1) {
            trace += '<br>';
        }
    }
    return trace;
}

function trace_section_title(title) {
    return '<div class="header">' + title + '</div>';
}

function trace_header(header) {
    return '<br><b>' + header + '</b><br/>';
}

function trace_error(message) {
    return '<div class="error">' + message + '</div><br/>'
}

function trace_sql(sql) {
    return '<div class="codeblock">' + sql + '</div>'
}

// Format trace results into tables
function trace_results(res) {
    let results;

    // Parse string to array or json object
    if (res[0] == "[" || res[0] == "{") {
        results = JSON.parse(res);
    }
    else {
        results = res;
    }

    // Parse results into array of results
    results = (Array.isArray(results)) ? results : [results]

    // Format results based on the result type
    if (typeof results[0] == "string") {
        return trace_list_str_results(results);
    }
    else if (typeof results[0] == "object") {
        return trace_list_dict_results(results);
    }
    return results;
}

// Format a list of dictionary to table
function trace_list_dict_results(results) {
    let trace_string = "<table border='1'><tr>";

    // Build key row
    let keys = Object.keys(results[0]);
    for (let k=0; k<keys.length; k++) {
        trace_string += "<th>" + keys[k] + "</th>";
    }
    trace_string += '</tr>';

    // Build results row
    for (let r=0; r<results.length; r++) {
        trace_string += '<tr>';
        for (let c=0; c<keys.length; c++) {
            let key = keys[c];
            let value = results[r][key] || "";
            trace_string += '<td>' + value + '</td>';
        }
        trace_string += '</tr>';
    }
    trace_string += '</table>';
  
    return '<div class="results">' + trace_string + '</div>';
}

// Format a list of string to rows
function trace_list_str_results(results) {
    let trace_string = '<table border="1">';

    for (let r=0; r<results.length; r++) {
        trace_string += '<tr><td>' + results[r] + '</td></tr>';
    }
    trace_string += '</table>';

    return '<div class="results">' + trace_string + '</div>';
}
