"""Sample secrets for testing redaction patterns."""

AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
AWS_SESSION_TOKEN = "FwoGZXIvYXdzEBYaDKxampleTokenContent123456"

GITHUB_PAT = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
GITHUB_OAUTH = "gho_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
GITHUB_APP = "ghs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

GITLAB_TOKEN = "glpat-xxxxxxxxxxxxxxxxxxxx"

SLACK_BOT_TOKEN = "xoxb-123456789012-1234567890123-abcdefghijklmnopqrstuvwx"
SLACK_USER_TOKEN = "xoxp-123456789012-1234567890123-abcdefghijklmnopqrstuvwx"
SLACK_WEBHOOK = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/123456789012345678/abcdefghijklmnopqrstuvwxyz"

PRIVATE_KEY_RSA = """-----BEGIN RSA PRIVATE KEY-----
MIIBogIBAAJBALRiMLAhQvbMD6XMj7pFLqCXe8f1v3pW7m8J7bVn9fEaZlGJ+hTq
K9xLQFJLLWPLiPECAwEAAQJABhd6gSvXhLrqXqYptB8p3m8F4lLXN9YyTT7d1qnZ
example_key_content_here
-----END RSA PRIVATE KEY-----"""

PRIVATE_KEY_EC = """-----BEGIN EC PRIVATE KEY-----
MHQCAQEEICg7E4cU3iYfU3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3f3
example_ec_key
-----END EC PRIVATE KEY-----"""

GCP_API_KEY = "AIzaSyDaGmWKa4JsXZ-HjGw7ISLn_3namBGewQe"

STRIPE_SECRET_KEY = "sk_live_4eC39HqLyjWDarjtT1zdp7dc"
STRIPE_RESTRICTED_KEY = "rk_live_4eC39HqLyjWDarjtT1zdp7dc"

NPM_TOKEN = "npm_abcdefghijklmnopqrstuvwxyz123456"

PYPI_TOKEN = "pypi-AgEIcHlwaS5vcmcCJGMwYjU0NDMxLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMAACGFsicHJvamVjdCI6InRlc3QtcHJvamVjdCJdAAIsSWYgeW91IGFyZSByZWFkaW5nIHRoaXMsIHlvdSBhcmUgYXdlc29tZSEK"

JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example"

BASIC_AUTH = "Basic dXNlcm5hbWU6cGFzc3dvcmQ="

POSTGRES_URL = "postgres://user:password123@localhost:5432/mydb"
MYSQL_URL = "mysql://root:secret@127.0.0.1:3306/database"
MONGODB_URL = "mongodb+srv://admin:pass@cluster.mongodb.net/db"
REDIS_URL = "redis://:secretpassword@redis.example.com:6379/0"

AZURE_CONNECTION = "DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz=="

SENDGRID_KEY = "SG.abcdefghijklmnopqrstuv.wxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZab"

TWILIO_KEY = "SKabcdef0123456789abcdef0123456789"

MAILCHIMP_KEY = "abcdef0123456789abcdef0123456789-us10"

PRIVATE_IP_1 = "10.0.0.1"
PRIVATE_IP_2 = "192.168.1.100"
PRIVATE_IP_3 = "172.16.0.50"

PUBLIC_IP = "203.0.113.50"

EMAIL_1 = "user@example.com"
EMAIL_2 = "john.doe+tag@company.co.uk"

INTERNAL_HOSTNAME = "server01.internal"
LOCAL_HOSTNAME = "db.local"

UUID_EXAMPLE = "550e8400-e29b-41d4-a716-446655440000"

SAMPLE_LOG_WITH_SECRETS = """
2024-01-15 10:30:45 INFO Starting application
2024-01-15 10:30:46 DEBUG Connecting to postgres://admin:supersecret@db.example.com:5432/prod
2024-01-15 10:30:47 INFO AWS Key: AKIAIOSFODNN7EXAMPLE
2024-01-15 10:30:48 ERROR Failed to authenticate with token ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2024-01-15 10:30:49 DEBUG Email notification sent to admin@company.com
2024-01-15 10:30:50 INFO Server listening on 192.168.1.100:8080
"""

SAMPLE_TRACEBACK_WITH_SECRETS = '''
Traceback (most recent call last):
  File "/home/alice/project/main.py", line 25, in connect
    client = boto3.client('s3', aws_access_key_id='AKIAIOSFODNN7EXAMPLE')
  File "/home/alice/.venv/lib/python3.10/site-packages/boto3/session.py", line 100, in client
    return self._session.create_client(...)
botocore.exceptions.ClientError: AWS key invalid: AKIAIOSFODNN7EXAMPLE
'''

SAMPLE_CONFIG_WITH_SECRETS = """
database:
  host: db.internal
  port: 5432
  user: admin
  password: "super_secret_password_123"
  
api:
  key: "sk_live_4eC39HqLyjWDarjtT1zdp7dc"
  endpoint: https://api.example.com
  
aws:
  access_key_id: AKIAIOSFODNN7EXAMPLE
  secret_access_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
"""

ALL_SECRETS = {
    "aws_access_key": AWS_ACCESS_KEY,
    "aws_secret_key": AWS_SECRET_KEY,
    "github_pat": GITHUB_PAT,
    "github_oauth": GITHUB_OAUTH,
    "gitlab_token": GITLAB_TOKEN,
    "slack_bot_token": SLACK_BOT_TOKEN,
    "slack_webhook": SLACK_WEBHOOK,
    "discord_webhook": DISCORD_WEBHOOK,
    "private_key_rsa": PRIVATE_KEY_RSA,
    "gcp_api_key": GCP_API_KEY,
    "stripe_secret_key": STRIPE_SECRET_KEY,
    "npm_token": NPM_TOKEN,
    "pypi_token": PYPI_TOKEN,
    "jwt_token": JWT_TOKEN,
    "postgres_url": POSTGRES_URL,
    "azure_connection": AZURE_CONNECTION,
    "sendgrid_key": SENDGRID_KEY,
    "email": EMAIL_1,
    "private_ip": PRIVATE_IP_1,
}
