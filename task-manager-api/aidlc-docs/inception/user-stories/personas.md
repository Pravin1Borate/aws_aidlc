# User Personas

## Persona: User

**Role**: Registered application user

**Description**: Any person who has created an account in the Task Manager API. All registered users share the same base permission set — access to resources is governed by ownership (creator) and assignment, not by role. A User is simultaneously a potential task creator (owner) and a potential task collaborator (assignee).

**Goals**:
- Register and authenticate securely to access their personal task workspace
- Create, organise, and track tasks through their full lifecycle (Todo → In Progress → Done)
- Set priorities and due dates to manage workload and deadlines
- Categorise and tag tasks for easy retrieval and organisation
- Assign tasks to colleagues and accept task assignments from others
- Quickly find specific tasks using status, priority, and due date filters

**Pain Points**:
- Losing track of task due dates and priorities across a growing task list
- Difficulty collaborating on tasks without clear ownership and assignment visibility
- Inability to filter tasks to focus on what matters right now
- Confusion about who is responsible for a task when multiple people are involved

**Technical Proficiency**: Comfortable with REST APIs; consumes the API via a client application or tool (e.g., curl, Postman, a frontend app)

**Permissions**:
- Can register and log in (public endpoints)
- Can create tasks (becomes owner)
- Can read, update their own tasks (owned or assigned)
- Can delete only tasks they own
- Can assign tasks to any registered user
- Can view other registered users (to select assignees)
- Cannot access or modify tasks they neither own nor are assigned to

**Story Mapping**:
- All stories in Epic 1 (Authentication)
- All stories in Epic 2 (Task Management)
- All stories in Epic 3 (Task Organisation)
- All stories in Epic 4 (Task Assignment)
- All stories in Epic 5 (Filtering & Discovery)
