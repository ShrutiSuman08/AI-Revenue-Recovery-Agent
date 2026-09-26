# RevenueOps Agent — Design & Limitations

## 1. Problem and Design Goal

Failed payments create recoverable revenue loss, but automatically retrying every
failure can create customer-experience and operational risk.

RevenueOps Agent is a bounded autonomous workflow that accepts a high-level
natural-language goal, creates a recovery plan, investigates failed payments,
recommends recovery strategies, validates them against deterministic business
policies, executes approved simulated actions, adapts to failures, and produces
an auditable final report.

The design objective is:

> **Maximize safe recoverable revenue subject to explicit recovery policies and
> bounded autonomous recovery attempts.**

The system is intentionally designed so that an LLM can recommend an action but
cannot independently authorize a financial operation.

---

## 2. Key Design Decisions

### LangGraph for Stateful Orchestration

LangGraph is used to model the recovery process as a stateful workflow.

This is useful because payment recovery is not a simple linear pipeline. An
execution can fail, the failure must become new evidence, and the workflow may
need to return to the reasoning stage before continuing.

The graph explicitly controls transitions between planning, analysis, policy
validation, execution, failure handling, replanning, case finalization, and
report generation.

### LLM Reasoning with Deterministic Guardrails

Groq-hosted LLMs are used where semantic reasoning is useful:

- generating the high-level recovery plan;
- diagnosing individual failed-payment cases;
- recommending recovery strategies;
- adapting recommendations after unsuccessful attempts.

Hard business constraints remain deterministic Python logic.

The central safety principle is:

> **The LLM proposes; deterministic policy authorizes; tools execute.**

This prevents the language model from bypassing recovery limits or directly
executing unrestricted financial actions.

### Structured Contracts

Pydantic models define contracts for plans, payment evidence, policy decisions,
recovery decisions, execution results, and final reports.

Structured outputs reduce ambiguity between the reasoning layer and the
deterministic workflow.

### Distinct Tool Responsibilities

The system separates observation, authorization, and execution:

1. **Payment Data Tool** — retrieves payment and recovery evidence.
2. **Policy Tool** — approves or blocks proposed recovery actions.
3. **Recovery Tool** — simulates approved recovery actions.

This separation makes tool use explicit and prevents reasoning and execution
from being collapsed into a single opaque LLM call.

### Bounded Replanning

Recovery failures are recorded as new evidence and supplied to the recovery
agent during the next reasoning cycle.

However, replanning is bounded. A case can experience at most two unsuccessful
autonomous recovery attempts before it is escalated to manual review.

This prevents infinite retry loops and establishes a clear human-intervention
boundary.

---

## 3. Failure and Recovery Design

The main robustness scenario is `PAY-004`.

The first `retry` execution for this payment is deliberately failed through
explicit fault injection.

The workflow must then:

1. detect the unsuccessful tool result;
2. record the failed action and failure type;
3. increment the case failure count;
4. treat the failure as new evidence;
5. invoke the recovery agent again;
6. allow a different recovery strategy to be proposed;
7. re-run deterministic policy validation;
8. execute the new action only if approved.

The alternative action may succeed, or another genuine simulated execution
failure may occur.

If the configured failure budget is exhausted, the workflow stops autonomous
recovery and sends the case to manual review.

The deliberate failure is explicitly identified as injected in the execution
trace. It is not presented as a naturally occurring external-provider failure.

---

## 4. Evaluation Approach

The evaluator uses six synthetic payment scenarios chosen to exercise different
workflow branches.

The scenarios include:

- successful retry recovery;
- insufficient-funds recovery;
- a high-value payment blocked by policy;
- deliberate execution failure followed by replanning;
- a payment with exhausted previous recovery attempts;
- a standard recoverable payment.

Three sample evaluation artifacts are included.

### `evaluation/logs/demo_run.json`

Records a complete autonomous batch execution, including planning, payment
analysis, policy decisions, recovery execution, failure handling, replanning,
case outcomes, and the final report.

### `evaluation/logs/policy_safety_demo.json`

Extracts the `PAY-003` policy-safety path from a recorded demo execution.

It demonstrates that an LLM recommendation can be rejected by deterministic
policy and that a blocked payment does not reach the recovery execution tool.

### `evaluation/logs/plan_repair_demo.json`

Demonstrates the planning-validation recovery path using a deliberately invalid
initial plan.

For deterministic evaluation, the external LLM repair response in this artifact
is mocked. The plan validation, repair-node state transition, and subsequent
revalidation are exercised, but the artifact should not be interpreted as a
recording of a live external LLM repair request.

Automated tests additionally verify workflow routing, policy blocking, injected
failure handling, bounded replanning, plan validation, and safe workflow
termination.

---

## 5. Limitations

### Simulated Recovery Execution

The recovery tool does not communicate with a real payment provider.

Successful recovery therefore means that the simulated recovery tool returned a
successful result; it does not represent money actually collected from a
customer.

### Synthetic Evaluation Data

The primary evaluator uses six deterministic synthetic payment scenarios.

The repository contains a SQLite-backed payment-data layer, but the evaluation
workflow intentionally uses the synthetic fixture to make important branches
repeatable and easy to demonstrate.

### No Real Customer Communication

Actions such as `request_alternate_payment` and `notify_and_retry_later` are
simulated strategies.

The project does not send email, SMS, push notifications, or payment links to
real customers.

### LLM Output Can Vary

Temperature is configured to zero, but external LLM output is not guaranteed to
be identical across every invocation.

Tests therefore focus primarily on safety and workflow invariants rather than
requiring one exact LLM recommendation for every case.

### High-Level Planning

The generated plan represents semantic intent rather than directly controlling
arbitrary graph execution.

The LangGraph workflow defines the permitted execution paths.

This is intentional: in a financial workflow, an LLM-generated plan should not
be able to dynamically create unrestricted execution paths or bypass policy
checks.

### Simplified Business Policies

The current policy engine demonstrates a small set of explicit constraints,
including automatic-recovery amount limits, supported actions, and recovery
attempt limits.

A production revenue-recovery system would require significantly richer
merchant, customer, payment-method, geography, risk, compliance, and
provider-specific policies.

### Limited Persistence During Evaluation

The evaluation workflow focuses on observable agent behavior and structured
execution traces.

It does not provide production-grade transactional persistence, distributed
locking, idempotency guarantees, or recovery across process crashes.

---

## 6. Productionization Requirements

A production version would require additional engineering beyond the scope of
this evaluation, including:

- authenticated payment-provider integrations;
- idempotent recovery operations;
- durable workflow checkpoints;
- transactional persistence;
- customer-notification integrations;
- authorization and role-based access controls;
- secrets management;
- provider rate-limit handling;
- retry and timeout policies for external APIs;
- monitoring and alerting;
- personally identifiable information protection;
- financial and regulatory compliance controls;
- human-review queues and approval workflows;
- production audit-log retention;
- larger offline and online evaluation suites.

The current project intentionally prioritizes agent planning, tool
orchestration, deterministic safety boundaries, failure recovery, auditability,
and explainable evaluation over production payment infrastructure.

---

## 7. Design Summary

RevenueOps Agent is designed as a **bounded autonomous system**, not an
unrestricted financial agent.

The LLM provides flexible reasoning where it is useful, while deterministic
code retains authority over business-policy enforcement and workflow safety.

The most important architectural property is therefore not simply that the
agent can recover a payment successfully, but that it can:

> **plan, act through explicit tools, observe failure, adapt using new evidence,
> respect deterministic constraints, stop when autonomy is exhausted, and
> explain what happened through a structured execution trace.**