# Ticketing

A simple support-ticketing system: customers report problems or requests as tickets, and agents work them through to resolution.

## Language

**Ticket**:
A problem or request reported by a customer, tracked through a lifecycle of states until it is closed.
_Avoid_: Issue, case

**Customer**:
A user who reports problems or requests by creating tickets, and can view their own tickets.
_Avoid_: Client, reporter

**Agent**:
A user who can view all tickets, reply to them, and change their status.
_Avoid_: Support staff, handler, admin

**User**:
An account that can log in; every user is either a customer or an agent.
_Avoid_: Account, member

**Reply**:
A message added to a ticket's conversation after creation, visible to the ticket's customer and any agent.
_Avoid_: Comment, message

**Priority**:
The urgency of a ticket: low, normal, high, or urgent.
_Avoid_: Severity, level

### Ticket lifecycle

**Open**:
The initial state of a new ticket, awaiting agent attention.
_Avoid_: New, pending

**In progress**:
An agent is actively working the ticket.
_Avoid_: Assigned, active

**Resolved**:
The agent considers the ticket handled; awaiting the customer's final decision.
_Avoid_: Done, fixed

**Closed**:
The terminal state; no further transitions.
_Avoid_: Cancelled, archived