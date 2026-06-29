# Requirements Verification Questions

Please answer the following questions by filling in the letter choice after each `[Answer]:` tag.
If none of the provided options match your needs, choose the last option (Other/X) and describe your preference.

Let me know when you're done answering.

---

## Section 1: Technical Stack

## Question 1
What programming language and framework should be used for the REST API?

A) Node.js with Express.js

B) Node.js with NestJS (TypeScript, structured, enterprise-ready)

C) Python with FastAPI

D) Python with Django REST Framework

E) Java with Spring Boot

X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 2
What database technology should be used?

A) PostgreSQL (relational, recommended for task management with relationships)

B) MySQL (relational, widely adopted)

C) MongoDB (NoSQL document database)

D) SQLite (lightweight, good for development/small scale)

X) Other (please describe after [Answer]: tag below)

[Answer]: For now keep it in json file.

---

## Question 3
What user authentication mechanism should be used?

A) JWT (JSON Web Tokens) — stateless, ideal for REST APIs

B) Session-based authentication with cookies

C) OAuth 2.0 / OpenID Connect (Google, GitHub login)

D) API Key authentication

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Section 2: Functional Requirements

## Question 4
What priority levels should tasks support?

A) Three levels: Low, Medium, High

B) Four levels: Low, Medium, High, Critical

C) Five levels: Very Low, Low, Medium, High, Critical

D) Numeric priority (1–5 or 1–10)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 5
Should tasks support assignment to specific users (task ownership/assignment)?

A) Yes — tasks can be assigned to any registered user

B) Yes — but only to the task creator themselves (personal task manager)

C) No — tasks are personal, each user manages only their own tasks

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 6
What task statuses should be supported?

A) Two statuses: Pending, Completed

B) Three statuses: Todo, In Progress, Done

C) Four statuses: Backlog, Todo, In Progress, Done

D) Five statuses: Backlog, Todo, In Progress, In Review, Done

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 7
Should tasks support categories or tags for organization?

A) Yes — categories (single category per task, predefined list)

B) Yes — tags (multiple tags per task, user-defined)

C) Yes — both categories and tags

D) No — priority and status are sufficient for organization

X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 8
Should the API support filtering and sorting tasks?

A) Basic filtering only: by status, priority, due date

B) Advanced filtering: by status, priority, due date, assignee, tags/categories

C) Filtering with full-text search on task title/description

D) No filtering required — return all tasks and let the client filter

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Section 3: Non-Functional Requirements

## Question 9
What is the expected deployment target for this API?

A) Local development only (no cloud deployment)

B) AWS (EC2, ECS, Lambda, or similar)

C) Docker container (any cloud or on-prem)

D) Heroku, Render, or similar PaaS

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 10
What is the expected scale/load for this API?

A) Small scale — personal use or small team (< 100 users)

B) Medium scale — startup/team use (100–10,000 users)

C) Large scale — enterprise use (10,000+ users)

D) Unknown/not yet determined

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 11
Should the API include rate limiting to prevent abuse?

A) Yes — implement rate limiting per user/IP

B) No — not required for this project

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Section 4: Extensions

## Question 12: Security Extensions
Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)

B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 13: Resiliency Extensions
Should the resiliency baseline be applied to this project?

**What this extension is.** Enabling it applies a set of directional, design-time best practices for building resilient systems, derived from the AWS Well-Architected Framework (Reliability Pillar). It steers requirements, design, and code toward fault tolerance, high availability, observability, and recoverability.

**What this extension is NOT.** It is a starting point that scaffolds good resiliency decisions early — it is not a substitute for a formal AWS Well-Architected Review of the built system.

A) Yes — apply the resiliency baseline as directional best practices (recommended for business-critical workloads)

B) No — skip the resiliency baseline (suitable for PoCs, prototypes, and experimental projects)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 14: Property-Based Testing Extension
Should property-based testing (PBT) rules be enforced for this project?

A) Yes — enforce all PBT rules as blocking constraints (recommended for projects with business logic, data transformations, or stateful components)

B) Partial — enforce PBT rules only for pure functions and serialization round-trips

C) No — skip all PBT rules (suitable for simple CRUD applications or thin integration layers)

X) Other (please describe after [Answer]: tag below)

[Answer]: A
