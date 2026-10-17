# Contributing an investigation

Every case must include:

1. Task and authority: what was requested and permitted.
2. Environment: exact versions, synthetic fixtures, and dependencies.
3. Trigger: precise failure boundary and reproduction command.
4. Observation: controller output versus actual system state.
5. Expected result: explicit invariant and independent oracle.
6. Repair: minimal behavioral change and tradeoffs.
7. Regression: a check shown failing before the repair and passing after it.
8. Limits: what the example does not establish.

Label constructed examples, reproduced public incidents, and privately disclosed issues distinctly. Do not name a third-party product as vulnerable without evidence and appropriate disclosure. Do not include credentials, customer data, or unreviewed claims of compliance.

Use real run counts for model experiments and report variation. Keep tests offline by default. No automatic publication or sending messages is part of the development workflow.
