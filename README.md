# ![](static/logo-header.png)

> [!NOTE]
> This project is for demonstration only and is not an officially supported
> Google product.
>
> If you're a Googler using this demo, please fill up this
> [form](https://forms.gle/dJUdMEbUu7k3TmT4A). If you're interested in using our
> hosted version, please fill up this
> [form](https://forms.gle/3AknwhhWv2pWw46Q8).

## Introduction

This project provides a production-quality reference implementation for building
Agentic applications that use [Agents] and [Retrieval Augmented Generation
(RAG)][rag] to query and interact with data stored in Google Cloud Databases.

This demonstration features Cymbal Air, a fictional airline. The application
showcases a customer service assistant that helps travelers manage flights and
find information about San Francisco International Airport (SFO), Cymbal Air's
hub. The agent can answer questions like:

* *Are there any luxury shops in the terminal?*
* *Where can I get coffee near gate A6?*
* *I need to find a gift for my colleague.*
* *What flights are headed to NYC tomorrow?*

[rag]: https://www.promptingguide.ai/techniques/rag
[Agents]: https://www.promptingguide.ai/agents/introduction

## Table of Contents
<!-- TOC depthfrom:2 -->

- [Understanding the demo](#understanding-the-demo)
    - [Retrieval Augmented Generation RAG](#retrieval-augmented-generation-rag)
    - [Agent-based Orchestration](#agent-based-orchestration)
    - [Architecture](#architecture)
- [Deployment](#deployment)
    - [Before you begin](#before-you-begin)
    - [One-Time Database & Tool Configuration](#one-time-database--tool-configuration)
    - [Launch the Toolbox Server Choose One](#launch-the-toolbox-server-choose-one)
    - [Running the Agentic Application](#running-the-agentic-application)
    - [Clean Up](#clean-up)
- [Customizing Your Tools](#customizing-your-tools)

<!-- /TOC -->

## Understanding the demo

### Retrieval Augmented Generation (RAG)

One of the best tools for reducing hallucinations is to use Retrieval Augmented
Generation (RAG). RAG is the concept of retrieving some data or information,
augmenting your prompt to the agent, and allowing it to generate more accurate
responses based on the data included in the prompt. This grounds the model’s
response, making it less likely to hallucinate. This technique is also useful
for allowing the agent to access data it didn’t have when it was trained. And
unlike fine-tuning, the information retrieved for RAG does not alter the model
or otherwise leave the context of the request - making it more suitable for use
cases where information privacy and security are important.

Cloud databases provide a managed solution for storing and accessing data in a
scalable and a reliable way. By connecting an agent to a cloud database,
developers can give their applications access to a wider range of information
and reduce the risk of hallucinations.


### Agent-based Orchestration

This application uses an Agent-based orchestration model. Instead of a static
chain of calls, the LLM acts as an intelligent Agent that decides which tools to
use and in what order. It is given a set of available tools, each with a
specific function (e.g., `find_flights`, `list_amenities`). Based on the user's
query, the agent reasons about the best tool to use to find the answer. This
"thought process" allows the agent to handle a wider variety of queries and to
break down complex questions into smaller, manageable steps.

### Architecture

![Overview](architecture.svg)

The architecture consists of three main components:
1. **Application** -- The user-facing agentic app that orchestrates the
   interaction between the user and the agent.
1. **MCP Toolbox** -- [MCP Toolbox](https://github.com/googleapis/genai-toolbox)
   is a middleware server that exposes the database operations as a set of
   tools. The LLM agent connects to the Toolbox to execute these tools. This
   provides a secure, scalable, and modular way to manage database interactions.
1. **Database** -- The database containing the data the agent can use to answer
   questions. For this application, the database used was intentionally designed
   to be interchangeable in order to make it easier to run this on your
   preferred database.

Using the Toolbox as an intermediary offers several advantages:

1. **Better Security** - The Toolbox handles authentication and authorization,
   preventing the agent from directly accessing the database and reducing the
   risk of security vulnerabilities.
1. **Better scalability** - Toolbox allows multiple different Agents to leverage
   it, as well as allowing it to scale independently. It allows for production
   best practices such as connection pooling or caching.
1. **Better recall** - Agents perform better when given smaller, discrete tasks
   they can use to accomplish larger goals. By mapping a specific action to a
   specific, pre-determined query, via tools, it significantly improves the
   agent's ability to leverage it successfully.

Head over to the official [MCP Toolbox
docs](https://googleapis.github.io/genai-toolbox/getting-started/introduction/)
for more details.

## Deployment

Deploying Cymbal Air app is a three-step process. You will first download the
necessary tools, then perform a one-time setup for your database and Toolbox
configuration, and finally launch the Toolbox server and the app.

### Before you begin

First, clone this repository and download the MCP Toolbox binary.

1.  **Clone the repository:**
      ```bash
      git clone https://github.com/GoogleCloudPlatform/genai-databases-retrieval-app.git
      cd genai-databases-retrieval-app
      ```
2.  **Download MCP Toolbox binary:**

      Follow [these
      steps](https://googleapis.github.io/genai-toolbox/getting-started/introduction/#installing-the-server)
      to download the binary. This involves running the following commands:
      ```bash
      # See the releases page for the latest version
      export VERSION=0.8.0
      curl -O https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
      chmod +x toolbox
      ```

### One-Time Database & Tool Configuration

Next, you must perform a one-time setup to create your database instance,
populate it with data, and create the `tools.yaml` configuration file. This
process uses the Toolbox binary you just downloaded.

> [!IMPORTANT]
> For detailed, step-by-step instructions, follow the **[Database Setup
> Guide](docs/database_setup.md)**.

> [!NOTE]
> If you have already configured your own database, you can skip this section.

### Launch the Toolbox Server (Choose One)

After your database is initialized and your `tools.yaml` file is created, you
must run the Toolbox server so the agentic app can connect to it. You can either
run it locally for development or deploy it to Cloud Run for a more robust
setup.

### **Option A:** Run Toolbox Locally

For local development and testing, you can run the Toolbox server directly from
your terminal. This is the quickest way to get started.

* **For instructions, follow the [guide to running the Toolbox
  locally](https://googleapis.github.io/genai-toolbox/getting-started/introduction/#getting-started).**

   The basic command will be:
   ```bash
   ./toolbox --tools-file "tools.yaml"
   ```

### **Option B:** Deploy Toolbox to Cloud Run

For a scalable and production-ready setup, you can deploy the Toolbox as a
service on Google Cloud Run. This provides a stable, shareable endpoint for your
application.

* **For instructions, follow the [guide to deploying the Toolbox on Cloud
  Run](https://googleapis.github.io/genai-toolbox/how-to/deploy_toolbox/)**.
</details>

### Running the Agentic Application

[Instructions for running app locally](docs/run_app.md)

### Clean Up

[Instructions for cleaning up resources](docs/clean_up.md)

## Customizing Your Tools

This demo can serve as a starting point for building your own Agentic
applications. You can customize the tools available to the agent by modifying
the MCP Toolbox configuration file.

Please refer to the [MCP Toolbox documentation][configure] for more information on creating
and configuring tools.

[toolbox]: (https://googleapis.github.io/genai-toolbox/getting-started/introduction/#getting-started)
[configure]: (https://googleapis.github.io/genai-toolbox/getting-started/configure/)