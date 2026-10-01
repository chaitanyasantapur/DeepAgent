# AWS Skill - Instructions

## Workflow

1. **Clarify the context silently**
   - Which services are involved? Which region? Greenfield or existing stack?
   - What is the deliverable: a design, a command, a policy, code, or a fix?
   - If the user has not said, assume `us-east-1`, a single AWS account, and the AWS CLI v2.

2. **Pick the right service** (see the selection guide below). State the choice and the one-line reason.

3. **Produce the artifact**
   - Policies: minimal JSON, one statement per purpose, resources scoped by ARN.
   - CLI: complete commands with every required flag.
   - boto3: a function that takes a client as an argument so it is testable, plus a short `__main__`.
   - IaC: a single self-contained snippet that would deploy as written.

4. **Call out operational concerns**
   - Security: encryption at rest and in transit, public access, logging.
   - Cost: the main cost driver and a rough order of magnitude.
   - Limits: service quotas that commonly bite (Lambda 15 min timeout, S3 5 GB single PUT, etc.).

5. **Verify facts** with `internet_search` when the question depends on current limits, pricing, or a recently launched feature. Cite the AWS docs URL.

## Service Selection Guide

| Need | Default choice | Choose instead when |
|---|---|---|
| Run code on demand | Lambda | Runs > 15 min, needs > 10 GB memory, or needs a persistent process: Fargate |
| Containers | ECS on Fargate | Team already runs Kubernetes: EKS |
| Virtual machines | EC2 (Graviton where possible) | Only if Lambda/Fargate truly cannot fit |
| Object storage | S3 | Never anything else for blobs |
| Relational DB | Aurora Serverless v2 (PostgreSQL) | Simple and small: RDS PostgreSQL; need MySQL compatibility: Aurora MySQL |
| Key-value / document | DynamoDB | Complex queries or joins: a relational DB |
| Cache | ElastiCache for Redis / Valkey | In-Lambda caching for tiny data |
| Queue | SQS (standard) | Strict ordering: SQS FIFO; pub/sub fan-out: SNS or EventBridge |
| Event bus | EventBridge | High-throughput streaming: Kinesis Data Streams or MSK |
| API | API Gateway HTTP API | Need WebSockets or request validation: REST API; need gRPC or long requests: ALB |
| Secrets | Secrets Manager | Plain config values: SSM Parameter Store |
| Static site | S3 + CloudFront | Server-side rendering: Amplify Hosting or Lambda@Edge |
| Auth | Cognito | Existing IdP: IAM Identity Center or federation |
| Observability | CloudWatch Logs + Metrics + X-Ray | Already on Datadog/Grafana: ship via Firehose or agent |

## IAM Rules

- One role per workload. Never share a role between unrelated services.
- Start from the AWS managed policy for the service and trim it, or write a custom policy from the actions the code actually calls.
- Use conditions (`aws:SourceArn`, `aws:SourceAccount`, `s3:prefix`) to narrow further.
- Trust policies must name the exact principal (`lambda.amazonaws.com`, a specific role ARN), never `"AWS": "*"`.
- Use IAM Access Analyzer to validate a policy before shipping it.
- Humans use IAM Identity Center with short-lived credentials. No long-lived access keys for people.

## Troubleshooting Checklist

- `AccessDenied` / `UnauthorizedOperation`: decode with `aws sts decode-authorization-message` if available, check the role's policy, then SCPs, then resource policies, then permission boundaries.
- `Could not connect to the endpoint URL`: wrong region or a typo in the service name. Check `AWS_REGION` and `aws configure list`.
- Lambda `Task timed out`: raise the timeout, check for a VPC without a NAT gateway, or an unawaited call.
- Lambda in a VPC cannot reach the internet: it needs a NAT gateway or VPC endpoints.
- S3 `403` on a public object: Block Public Access is on at the bucket or account level. Prefer CloudFront with Origin Access Control over public buckets.
- RDS connection refused: security group inbound rule, subnet route, or the DB is not publicly accessible and the client is outside the VPC.
- `ThrottlingException`: add exponential backoff (boto3 has `retries={"mode": "adaptive"}`) and request a quota increase.
- CloudFormation `ROLLBACK_COMPLETE`: read the first failed event in the stack events, not the last one.

## Cost Guardrails

- Turn on Cost Explorer and set an AWS Budgets alert in every account.
- Tag everything with `Project`, `Environment`, `Owner`.
- The usual surprises: NAT gateway hourly and data processing, cross-AZ data transfer, CloudWatch Logs ingestion, idle RDS instances, unattached EBS volumes and old snapshots.
- Use S3 Intelligent-Tiering or lifecycle rules for data that is rarely read.

## Infrastructure as Code Conventions

- CDK: one stack per deployable unit, constructs for reuse, `cdk diff` before `cdk deploy`.
- Terraform: remote state in S3 with DynamoDB locking (or S3 native locking on recent versions), one workspace per environment, pin provider versions.
- CloudFormation: use `Parameters` for environment differences and `Outputs` for cross-stack values.
- Never store state or secrets in the repo.
