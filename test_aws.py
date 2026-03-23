# Add this near the top, before creating the session
os.environ.setdefault("AWS_ENDPOINT_URL", "http://localhost:4566")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")

# Then update the session creation to include endpoint_url
ENDPOINT = os.getenv("AWS_ENDPOINT_URL")

session = boto3.Session(
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1"
)

def c(service):
    return session.client(service, endpoint_url=ENDPOINT,
                          region_name="us-east-1")