# Requirements Clarification Questions

I detected one contradiction in your responses that needs resolution, plus the Resiliency extension you enabled requires a few mandatory follow-up questions during requirements analysis.

Please answer each question by filling in the letter choice after the `[Answer]:` tag.

---

## Contradiction 1: Rate Limiting vs. Security Rules

You indicated **No rate limiting** (Q11:B) but also **Enable all Security rules as blocking constraints** (Q12:A).

These responses are contradictory because **SECURITY-11** (Secure Design Principles) explicitly requires:
> "**Rate limiting**: Public-facing endpoints MUST implement rate limiting or throttling to prevent abuse"

This is a blocking constraint — the Security extension cannot be enabled without addressing this.

### Clarification Question 1
How should the rate limiting conflict be resolved?

A) Add rate limiting — implement lightweight rate limiting per user/IP (satisfies SECURITY-11, keeps Security rules enabled)

B) Disable rate limiting AND disable Security extension — remove SECURITY rules from this project (suitable for local PoC)

C) Apply Security rules but document rate limiting as a known deferred item with explicit justification (partial compliance approach)

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Resiliency Mandatory Questions

You enabled the Resiliency baseline extension (Q13:A). The following questions are mandatory before finalizing requirements (per RESILIENCY-02, RESILIENCY-03).

---

### Clarification Question 2: RTO/RPO Goals and Disaster Recovery Strategy (RESILIENCY-02)
What are your Recovery Time Objective (RTO) and Recovery Point Objective (RPO) goals? These determine the appropriate Disaster Recovery strategy.

**Note**: Since you selected local development only (Q9:A), most DR options may be N/A for this project phase.

A) RPO/RTO: Hours — Backup & Restore strategy. Lowest cost. Suitable for non-critical workloads.

B) RPO/RTO: 10s of minutes — Pilot Light strategy. Data live, services idle on failover.

C) RPO/RTO: Minutes — Warm Standby strategy. Services run at reduced capacity, scaled up on failover.

D) N/A — This is a local development project only. No DR requirements at this stage.

X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Clarification Question 3: Change Management Process (RESILIENCY-03)
How should production changes for this workload be governed?

A) Use our existing organizational change management process (provide name/tool after [Answer]: tag)

B) No formal process — propose a lightweight change management process

C) N/A — This is a local development / experimental project, exempt from formal change management

X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

### Clarification Question 4: Regional Topology (RESILIENCY-08)
Does this workload require multi-region deployment, or is single-region sufficient?

**Note**: Given local development scope (Q9:A), this may be N/A.

A) Single-region, multi-zone — tolerates zone failure, not full-region failure

B) Multi-region active-passive — survives region failure with failover

C) N/A — Local development only, no cloud deployment at this stage

X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

### Clarification Question 5: Incident Response Process (RESILIENCY-15)
How are production incidents handled for this workload?

A) Use our existing incident response process (provide reference after [Answer]: tag)

B) No formal process — propose a lightweight incident response process

C) N/A — Local development only, no production incident response needed at this stage

X) Other (please describe after [Answer]: tag below)

[Answer]: C
