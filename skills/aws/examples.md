# AWS Skill - Examples

## Example 1: Least-privilege IAM policy

**User:** I need a policy that lets my Lambda read objects from the `invoices-raw` bucket and write to `invoices-processed`.

**Good answer:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadRaw",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::invoices-raw/*"
    },
    {
      "Sid": "ListRaw",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::invoices-raw"
    },
    {
      "Sid": "WriteProcessed",
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": "arn:aws:s3:::invoices-processed/*"
    }
  ]
}
```

Attach it to the Lambda execution role along with `AWSLambdaBasicExecutionRole` for CloudWatch Logs. `ListBucket` is on the bucket ARN, object actions are on `bucket/*`. That split is the most common mistake.

## Example 2: CLI task

**User:** How do I copy everything from one bucket to another in a different region?

**Good answer:**

```bash
aws s3 sync s3://<source-bucket> s3://<dest-bucket> --source-region us-east-1 --region eu-west-1
```

For buckets over a few hundred GB, use S3 Batch Operations or turn on Cross-Region Replication instead. Cross-region data transfer is billed, roughly 2 cents per GB at the time of writing. Confirm on the S3 pricing page for your regions.

## Example 3: boto3 code

**User:** Write Python that uploads a file to S3 and returns a presigned URL valid for one hour.

**Good answer:**

```python
"""Upload a file to S3 and return a one-hour presigned download URL."""

from pathlib import Path

import boto3
from botocore.client import BaseClient


def upload_and_presign(s3: BaseClient, bucket: str, path: Path, key: str | None = None) -> str:
    key = key or path.name
    s3.upload_file(str(path), bucket, key)
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=3600,
    )


if __name__ == "__main__":
    client = boto3.client("s3", region_name="us-east-1")
    print(upload_and_presign(client, "<bucket>", Path("report.pdf")))
```

Credentials come from the default chain (environment, SSO profile, or instance role). Install with `uv add boto3`.

## Example 4: Architecture question

**User:** We get about 2,000 webhook calls a minute and need to process each one within a few seconds. What should we use?

**Good answer:**

API Gateway HTTP API -> SQS -> Lambda.

- API Gateway writes directly to SQS with a service integration, so no Lambda is in the request path and the webhook sender gets a fast 200.
- SQS absorbs bursts. 2,000 per minute is about 33 per second, well inside standard-queue limits.
- Lambda consumes with batch size 10 and reserved concurrency so a downstream outage does not scale you to zero wallet.
- Add a dead-letter queue after 3 receives and a CloudWatch alarm on `ApproximateAgeOfOldestMessage`.

Cost at this volume is dominated by Lambda invocations and is on the order of tens of dollars per month. Check the Lambda and SQS pricing pages for your region.

## Example 5: Troubleshooting

**User:** My Lambda in a VPC times out when calling a third-party API.

**Good answer:**

A Lambda attached to private subnets has no route to the internet by itself. Fix one of:

1. Add a NAT gateway in a public subnet and a `0.0.0.0/0` route from the Lambda subnets to it. Simple, costs about 32 dollars a month per AZ plus data.
2. If the Lambda only needs AWS services, use VPC endpoints instead and skip NAT entirely.
3. If the Lambda does not need VPC resources at all, remove the VPC configuration.

Check with: `aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=<subnet-id>`.

## Example 6: CDK snippet

**User:** CDK in Python for a DynamoDB table with on-demand billing and a TTL attribute.

**Good answer:**

```python
from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as ddb
from constructs import Construct


class SessionsStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        ddb.Table(
            self,
            "Sessions",
            partition_key=ddb.Attribute(name="session_id", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="expires_at",
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
```

`expires_at` must be an epoch-seconds number on each item. Deploy with `cdk deploy`.
