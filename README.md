# AI Drive-Thru System

An intelligent drive-thru ordering system powered by multiple AI agents that understand natural language, process orders, and manage complex customer interactions in real-time.

![System Architecture](system-design.png)

## Overview

This system transforms traditional drive-thru ordering by using AI agents to understand customer speech, extract order details, handle modifications, and provide intelligent responses. Customers can speak naturally while the system processes their requests through a sophisticated agent-based workflow.

## AI Agents

The system uses six specialized AI agents, each powered by OpenAI's GPT-4o:

- **Intent Classification Agent**: Determines what the customer wants (add item, modify, remove, ask question)
- **Item Extraction Agent**: Extracts menu items, quantities, and special instructions from natural speech
- **Modify Item Agent**: Handles complex modification requests and identifies target items
- **Clarification Agent**: Asks intelligent follow-up questions when customer intent is unclear
- **Question Agent**: Answers customer questions about menu items, prices, and availability
- **Remove Item Agent**: Processes item removal requests with context awareness

## Key Features

- **Natural Language Processing**: Customers can order using conversational speech
- **Multi-Agent Architecture**: Specialized AI agents handle different aspects of the ordering process
- **Real-Time Voice Processing**: Live speech-to-text with immediate AI response
- **Intelligent Order Management**: Automatic item resolution, modification handling, and error recovery
- **Multi-Tenant Support**: Each restaurant can have its own menu and branding
- **Admin Dashboard**: Complete restaurant management interface

## Technology Stack

### AI & Machine Learning
- **OpenAI GPT-4o**: Core language model for all AI agents
- **LangChain**: Agent orchestration and structured output
- **Speech-to-Text**: Real-time voice processing
- **Natural Language Understanding**: Intent classification and entity extraction

### Backend
- **FastAPI**: High-performance async API framework
- **Tortoise ORM**: Modern async ORM with PostgreSQL
- **PostgreSQL**: Primary database with multi-tenant architecture
- **Redis**: Caching and session management
- **AWS S3**: File storage for images and audio

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Full type safety across the application
- **Tailwind CSS**: Utility-first styling
- **Real-time Updates**: Live order management interface

### Infrastructure
- **Docker**: Containerized deployment
- **AWS ECS**: Scalable container orchestration
- **Terraform**: Infrastructure as code
- **Multi-environment**: Development, staging, and production configs
