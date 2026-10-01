---
name: aws
description: Design, explain, and troubleshoot AWS architectures and write AWS CLI, boto3, CloudFormation, CDK, and Terraform snippets. Covers IAM, S3, Lambda, EC2, ECS/EKS, RDS, DynamoDB, VPC, CloudWatch, and cost questions.
license: MIT
compatibility: AWS CLI v2, boto3 1.34+, Python 3.11+
---

# AWS Skill

Use this skill for anything that touches Amazon Web Services: architecture advice, service choice, IAM policies, infrastructure as code, CLI commands, boto3 code, debugging errors, and cost estimates.

## When to Use

- The user names an AWS service or an AWS error message
- The user asks how to deploy, host, store, queue, or secure something "in the cloud" and AWS is the stated or default provider
- The user asks for an IAM policy, bucket policy, or trust policy
- The user asks for a CloudFormation, CDK, or Terraform snippet for AWS resources

## Supporting Files

Read these with `read_file` (pass `limit=1000`) before answering non-trivial requests:

- `instructions.md` - decision workflow, service selection guide, IAM rules, troubleshooting steps
- `examples.md` - worked examples of requests and good answers

## Quick Rules

1. Least privilege always. Never suggest `"Action": "*"` or `"Resource": "*"` without an explicit warning and a scoped alternative.
2. Prefer managed and serverless services unless the user states a reason not to (Lambda before EC2, Aurora Serverless or DynamoDB before self-managed databases).
3. Always state the region assumption and remind the user that pricing and availability vary by region.
4. Show CLI commands as `aws <service> <operation> --flag value`, one command per line, with placeholder values in `<angle-brackets>`.
5. Prefer boto3 for Python examples; use `boto3.client` for single operations and `boto3.resource` only where it simplifies code noticeably.
6. For infrastructure as code, default to CDK in Python for new projects and Terraform if the user already uses it. CloudFormation YAML when the user asks for it.
7. Pricing changes often. For cost questions, use `internet_search` to confirm current numbers and cite the AWS pricing page.
8. Never print, log, or hardcode credentials. Point to IAM roles, instance profiles, or `aws configure sso`.
