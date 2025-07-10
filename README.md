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

- [Introduction](#introduction)
- [Table of Contents](#table-of-contents)
- [Understanding the demo](#understanding-the-demo)
    - [Retrieval Augmented Generation (RAG)](#retrieval-augmented-generation-rag)
    - [Agent-based Orchestration](#agent-based-orchestration)
    - [Architecture](#architecture)
- [Deployment](#deployment)
    - [Before you begin](#before-you-begin)
    - [Toolbox Setup](#toolbox-setup)
    - [Database Setup](#database-setup)
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

Deploying this demo consists of 3 steps:
1. Toolbox Setup -- Deploying the MCP Toolbox and configuring it to connect to
   your database.
1. Database Setup -- Creating your database and initializing it with
   sample data
1. Running the Agentic Application -- Running your agentic application locally.

### Before you begin

Clone this repo to your local machine:
```bash
git clone https://github.com/GoogleCloudPlatform/genai-databases-retrieval-app.git
```

### Toolbox Setup

This app uses the MCP Toolbox to provide the tools for the LLM agent.

Setup the Toolbox server by following the instructions in the [MCP Toolbox
repository][toolbox].

### Database Setup

To use Cymbal Air, you must set up a supported Google Cloud database and
populate it with sample data. This process involves creating a database
instance, configuring environment variables, and using the MCP Toolbox to load
the data.

For detailed, step-by-step instructions on setting up your database, please
refer to the **[Database Setup Guide](docs/database_setup.md)**.

> [!NOTE]
> If you have already configured your own database, you can skip this section.

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