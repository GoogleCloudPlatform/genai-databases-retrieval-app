# Database Query Extension

Note: This project is experimental and is not an officially supported Google
product.


## Introduction

The Database Query Extension is a easy to customize demonstration of how to
extend an LLM-based application using cloud databases for advanced [Retrieval
Augmented Generation (RAG)][rag]. The demo is a full, end to end application
demonstrating a real world use-case. 

This repository is organized into several directories:

| Directory                                    | Description                                                                   |
|----------------------------------------------|-------------------------------------------------------------------------------|
| [`data`](/data)                              | Contains CSV files with the dataset for a working demo.                       |
| [`extension-service`](/extension-service)    | Contains the service for extending an LLM with information from the database. |
| [`langchain_tools_demo`](/extension-service) | Contains an LLM-based application that that uses the extension service.       |

[rag]: https://www.promptingguide.ai/techniques/rag

## Table of Contents
<!-- TOC -->

- [Database Query Extension](#database-query-extension)
    - [Introduction](#introduction)
    - [Table of Contents](#table-of-contents)
    - [Architecture Overview](#architecture-overview)
    - [Deploying](#deploying)
        - [Configuring the Database](#configuring-the-database)
        - [Deploying the Extension Service](#deploying-the-extension-service)
        - [Running the LLM-based Application](#running-the-llm-based-application)
    - [Customization](#customization)

<!-- /TOC -->

## Architecture Overview

![Overview](./architecture.png)

This demo contains 3 key parts:
1. **Application** -- the LLM-based app that acts as the interface between. In
   our example, the app is an Airport Assistant for the SFO airport, designed to
   help users navigate their trips to the airport. 
1. **Extension** -- Our extension provides the LLM-based application concrete,
   discrete actions that interact with the database. 
1. **Database** -- The database in our demo is interchangeable, making it easy
   to configure based on your needs.

Running the extension as a separate service has many benefits: 
1. **Better Recall** - It helps map specific actions to specific query,
   improving the LLMs ability to leverage it correctly. 
1. **Better scalability** - It allows the extension to scale independently from
   the LLM application, which opens the door for optimizations like caching
   queries and connection pooling for reduced overhead. 
1. **Better security** - It allows the extension and the application to handle
   security concerns like authentication and authorization independently from
   the LLM. 
## Deploying

This demo contains all the parts for a working application demonstrating

### Configuring the Database

The extension service uses a configurable 'datastore' interface that makes it
easy to deploy and test it with different databases. Choose the database that
best fits your use case, or perhaps you are already familiar with: 

// TODO: complete this link
* [Set up and configure AlloyDB][]

### Deploying the Extension Service

// TODO: instructions for deploying the extension service

### Running the LLM-based Application

// TODO: Instructions for running app locally

## Customization

This demo is intended not only demonstrate how to write extensions, but also as
a convenient start point to building your own extensions. Free free to clone or
fork this repo to jump start your own extension development. Keep in mind the
following tips:

1. **Use specific actions** -- It's tempting to expose your database through
   generic interfaces and hoping that the LLM will figure out how best to query
   the data. In practice, we've seen better results using specific, targeted
   actions mapped to pre-written queries. This significantly improves the
   accuracy and quality of responses using the extension.
2. **Think about security** -- LLM-based applications don't have discrete
   responses, which makes securing them difficult. Avoid letting the LLM provide
   input or make decisions that have security-related consequences -- instead,
   rely on your application,  extensions, and database working together in
   more-traditional ways to make sure only the information intended is exposed
   to the LLM or the user. 



