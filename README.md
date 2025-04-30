# Elevate Backend

Elevate Davao is a first-of-its-kind digital ecosystem map and collaboration platform built to supercharge the region’s innovation hub. By plotting every startup, investor, accelerator, and support organization on an interactive, searchable map, Elevate Davao turns geographic proximity into powerful connections—so you can discover local partners, mentors, and funding sources with a single click.

This repository contains the backend infrastructure built with AWS CDK, featuring GraphQL API, authentication, and AI-powered features.

---

## 🔧 Prerequisites

- Python 3.12
- Poetry (Python package manager)
- AWS CLI configured with appropriate credentials
- Node.js and npm (for CDK)

---

## 🚀 Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Activate virtual environment:
   ```bash
   poetry shell
   ```
4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

---

## 💻 Available Commands

### Development

- `poetry install` – Install project dependencies
- `poetry shell` – Activate virtual environment
- `poetry add <package>` – Add new dependency
- `poetry update` – Update dependencies
- `poetry add <package> --group <group>` – Add dependency to specific group (dev/rag_api/suggestions)

### Infrastructure (CDK)

- `cdk ls` – List all stacks
- `cdk synth` – Synthesize CloudFormation template
- `cdk diff` – Compare deployed stack with current state
- `cdk deploy` – Deploy stack to AWS
- `cdk destroy` – Remove deployed stack

### Code Quality

- `pre-commit install` – Set up git hooks
- `pre-commit run --all-files` – Run all pre-commit hooks
- `ruff check .` – Run linter
- `ruff format .` – Format code
- `pytest` – Run tests

---

## 🗂️ Project Structure

```
├── infra/             # CDK infrastructure code
│   ├── appsync/       # GraphQL API configuration
│   ├── cognito/       # Authentication setup
│   ├── dynamodb/      # Database tables
│   ├── functions/     # Lambda functions
│   ├── layers/        # Lambda layers
│   └── s3/            # Storage configuration
├── schema/            # GraphQL schema definitions
├── src/               # Application source code
├── tests/             # Test files
└── scripts/           # Utility scripts
```

---

## 🚢 Deployment

The project supports multiple deployment stages:

- `dev2`
- `dev`
- `staging`
- `prod`

To deploy to a specific stage:

```bash
make deploy_dev
```

---

## 🔐 Features

### Authentication

- User registration and login via Cognito
- Identity Pool for AWS service access

### API Capabilities

- GraphQL API with AppSync
- Real-time subscriptions
- Fine-grained access control

### Lambda Functions

- Email sending capability
- Analytics processing
- Profile management
- LLM-powered suggestions
- RAG (Retrieval-Augmented Generation) API

### Storage

- S3 bucket for general file storage
- DynamoDB for entity storage

### Scheduled Tasks

- Automated suggestions generation
- Periodic data processing

---

## 🔒 Security

- Pre-commit hooks for security scanning
- Secrets detection
- AWS best practices implementation
- Environment-based configuration

---

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

---

### 🎉 Enjoy!
