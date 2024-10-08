# Challenge: Email Throttle

## 1. Introduction
### Challenge
Create a service that accepts the necessary information and sends emails. It
should provide an abstraction between two different email service providers.
If one of the services goes down, your service can quickly failover to
a different provider without affecting your customers. More information go to [REVIEW](./REVIEW.md).

### Overview
This project is a system consisting of a back-end API, an email throttle service, and a minimal front-end, designed to demonstrate a clean and maintainable client/service architecture. The back-end exposes a RESTful JSON API, and the front-end is a [nothing at the moment]<!--single-page application with a simple `index.html` that links to the necessary JS/CSS files.-->

### Objective
The goal of this project is to provide a production-ready codebase that clearly demonstrates good engineering practices, including a clean separation between the front-end and back-end, high code quality, and proper testing. The project aims to showcase the chosen technologies and frameworks, with an emphasis on clarity, correctness, and maintainability.

### Features
- API
  - FastAPI
  - Swagger integration
  - in the container is using uvicorn
- CLI
  - argparser
- Core
  - middleware implementation (for retry, circuit breaker and rate limiter)
  - logging
- Local Deployment
  - rabbitmq + docker-composes
- Testing
  - unit tests with pytest
  - coverage with pytest-cov
- Development Environment
  - vscode
  - docker
  - pre-commit
    - formatter: flake8+black, isort
    - security: bandit
  - virtual env: pyenv
  - python version: 3.12.2
  - direnv (not required)

**NOT DONE YET**
- CI/CD
- Production Deployment
- Authentication and Authorization
- Monitoring and Alerting
- Documentation
- Email Vendors
- Better implementation of Rabbit Consumer and Producer
  - Middleware for serialize and deserealize
  - entities (aka dto's|entities|protobuf|...) for serialization and deserialization (EmailDTO is being used, but it is not its purpose!)
- Better implementation of Middlewares
  - using redis to save shared variables

### Technical stack
#### **Back-end**: The back-end is divided into three main components:
  - **Email Throttle**: Responsible for sending emails, ensuring that requests are managed efficiently.
  - **REST API**: Exposes the email throttle service, allowing other services to interact with it through a RESTful interface.
  - **CLI**: Provides a command-line interface to interact with the email throttle service. Currently, it [just] includes a simulator for testing and demonstration purposes.

**Email Throttle(/core)**
This module is responsible for the core functionality of the system: sending emails.
It includes various interfaces and base classes that allow the creation of different types of "senders."
The main components are:

- `Middlewares`: These are used to implement some form of "throttle" in email sending, following one of the strategies mentioned in the design patterns. Current implementations: `CircuitBreaker`, `Retry`, `RateLimiter`.
- `Service`: This component is responsible for executing the middleware pipeline, where the final step involves sending emails via a vendor that has implemented the `EmailSender` interface.
- `Failover`: This component is responsible for implementing the "failover" strategy. When a service invocation pipeline fails, it should select a new pipeline with a different vendor. There are two implementations, but more strategies can be added in the future.


**API**

**How could the API communicate with the Email Throttle/Core?**

- Directly as a module, similar to how the CLI uses the `simulate` command (monolith architecture).
- Through an intermediary, like a message queue (a handler would be needed) (distributed architecture).

Both approaches have their pros and cons. The first option is easier to implement but requires multiple instances of the same API if you need to handle a lot of requests.
This could lead to a potential architectural change, like implementing an API Gateway. Scaling the entire component together isn't always the best idea because handling
more client requests doesn't necessarily mean more emails will be sent.

The second option is a bit more robust but requires setting up a QUEUE (like RabbitMQ) to store the messages to be sent. This approach allows you to scale the components individually. Digging deeper into the problem of a monolithic setup, the bottleneck is always going to be the email sending services (vendors or external services), so scaling up the Email Throttle Core might not actually improve the app's performance.

In this sense, it seems more efficient to keep the architecture separated into API and Core instances, which increases the "guarantee of eventual delivery"—meaning that the email will be sent at some point.
It's worth noting that using a queue requires creating a Dead Letter Queue for failed emails, so they can be retried and configured accordingly, but it seems like the most scalable and hassle-free solution.

**Current Implementation**
The API offers two endpoints:
- POST /email
  - Send a single email using a fake sender

- POST /email/bulk
  - send multiples emails using a queue acting as a throttler
  - a default consumer is handling the messages.

**CLI**

- Simulator
Command: `email-throttle-core-cli simulate ...`
The execution flow is:
```CLI -> Simulator -> Create Required Configuration -> Execute the Sender```

There are two alternatives to send emails from the CLI, one is EmailFailover and EmailFailoverWithState.
Both have a similar behavior, in case a service fails, it will retry with the next service.
The main difference is with EmailFailoverWithState will keep track of the usage of last available service, and it may start again when the last service in the list fails.
With EmailFailover, it will always try to send an email using the first available service, and if all the services failed, it will return an error. The approach with
state never fails, so this approach could be called "eventually sended". Both have drawbacks that could be solved in future cycles.

- Consumer
Command: `email-throttle-core-cli consume ...`

This command creates a consumer that will be listening for messages in the queue and will send them using the configured services.
It is using a default configuration, for future implementations it will be possible to configure it with real services and configurations, similar than the simulate command.
(At the moment is using some methods from the simulate endpoint)


#### **Front-end**: The front-end is a [nothing at the moment]<!--a single-page application with a simple `index.html` that links to the necessary JS/CSS files. -->

## 2. System Architecture
### Design Patterns

#### Failover
- **Description**: The system automatically switches to an alternative service when a failure occurs in the primary service.
- **Solution**: Ensures continuity of service by switching to another available service without affecting the client experience.
- Classes: `EmailFailover` and `EmailFailoverWithState`.

#### Circuit Breaker
- **Description**: Prevents failures in one component (e.g., email service) from propagating to other components by interrupting the request flow when an issue is detected.
- Classes: CircuitBreaker
- **States**:
  - **Open**: Upon failure, requests are not sent for a set period.
  - **Half-open**: After the set period, a test request is sent; if successful, the circuit closes.
  - **Closed**: If the test request fails, the circuit reopens.

#### Rate Limiting
- **Description**: Controls the rate of requests to prevent overloading services and incurring unnecessary costs.
- Classes: RateLimiter
- **Considerations**:
  - **Rate**: Number of allowed requests.
  - **Window**: Time frame in which the requests are made.

#### Retry
- **Description**: Attempts to re-invoke the service if a failure occurs.
- Classes: Retry
- **Considerations**:
  - **Retry Attempts**: Maximum number of retry attempts.
  - **Backoff Strategy**:
    - **Immediate**: Retry immediately after failure.
    - **Constant**: Waits a fixed time between retries.
    - **Variable**: Waits a time determined by a criterion (e.g., exponential backoff).

### System Design

Current Architecture:
- with the single email sender, it sends the email directly
- with the bulk email sender, it sends the email to a queue and then processes with the consumers

#### Alternatives to consider:
##### Single-process
- **Description**: A single process manages all services, receiving all the emails and sending it. The case of the CLI is an example of this case.

##### Multi-process with Shared Variables
  - **Description**: Utilizes variable sharing tools and concurrency.
  - **Considerations**:
    - Complexity arises when trying to scale for independent microservices.
    - Working with multiprocess is more complex than working with a single process.

##### Microservices
- **Description**: Combines single and multi-process architectures, where containers may be single or multi-process. One container may have one or multi process to handle the email requests and sendings. The sharing memory is being done with redis.


## 4. Usage

###  Setup and Installation
Install [pyenv](https://github.com/pyenv/pyenv) or other tools to manage python versions.

```bash
pyenv install 3.12.2
python shell 3.12.2 # should be automatic activated
python -m venv .venv
source .venv/bin/activate
pip install -r . # this install all the requirements and CLI
pre-commit install
```


### Basic Commands

Running CLI
```bash
email-throttle-cli simulate -h
email-throttle-cli simulate \
    --email-count 30 --vendor-count 1 \
    --vendors vendor --middlewares retry,rl  \
    --retries 10 --rate-limiters 5,10
```

Running Tests (with coverage)
```bash
# it shows the coverage over the src code through the pytest-cov module
pytest
```

Running with Containers
```bash
# create the containers
docker-compose up -d

# invoke
for i in {1..100}; do
curl -X 'POST' \
    'http://127.0.0.1:3000/email/bulk' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '[
    {
        "subject": "string",
        "body": "string",
        "to": [
            "string"
        ],
        "from_email": "string"
    },
    {
        "subject": "string",
        "body": "string",
        "to": [
            "string"
        ],
        "from_email": "string"
    }]'
done

# take a look into logs within containers

```

Running Backend
```bash
fastapi dev src/email_throttle/api/main.py --port 3000
```

#### Running Swagger
- Start the containers or run the backend
- go to http://127.0.0.1:3000/docs


<!-- ## 6. Logging, Monitoring and Alerting
- **Logging**: Using default logger with [Loguru](https://github.com/Delgan/loguru).
- **Metrics Collection**:
- **Alerting**:  -->


<!-- ## Features
- [ ] Backend
    - [ ] CLI
    - [ ] API
    - [ ] Core (Email Throttle)

- [ ] Testing
    - [ ] Unit
    - [ ] Integration

- [ ] Frontend
    - [ ]

- [ ] Deployment
    - [ ] Locally with Containers
    - [ ] Cloud (AWS, Azure)

- [ ] Observability
    - [ ] Logging
    - [ ] Metrics
    - [ ] Monitoring -->
