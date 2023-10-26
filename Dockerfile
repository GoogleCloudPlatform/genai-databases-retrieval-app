# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Dockerfile for Cloud Run Job to initialize AlloyDB data

# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-bullseye

# Install PostgreSQL client
RUN apt-get update && apt-get install -y postgresql-client && apt-get clean

# Execute next commands in the directory /workspace
WORKDIR /workspace

# Copy local code and data to the container image
COPY data ./data
COPY extension_service ./extension_service

# Install dependencies
RUN pip install -r ./extension_service/requirements.txt

# Copy the script to the container image
COPY database_init.sh ./
# Ensure executable
RUN chmod +x database_init.sh

# Run script on container startup
CMD ["./database_init.sh"]
