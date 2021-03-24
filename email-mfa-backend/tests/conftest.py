import pytest
import os
import boto3


class LambdaContext:
    def __init__(self):
        self.function_name = "test"
        self.function_version = "$LATEST"
        self.invoked_function_arn = (
            "arn:aws:lambda:ap-northeast-1:123456789012:function:test"
        )
        self.memory_limit_in_mb = 128
        self.aws_request_id = "6748f6f8-cc75-14eb-e97b-20023a3a9277"
        self.log_group_name = "/aws/lambda/test"
        self.log_stream_name = (
            "2021/02/25/[$LATEST]97b9484a9204301be5ac034b952891b9"
        )


@pytest.fixture
def lambda_context():
    return LambdaContext()


@pytest.fixture(scope="session", autouse=True)
def init_ses():
    ses = boto3.client("ses", endpoint_url=os.getenv("AWS_ENDPOINT_URL"))
    ses.verify_email_identity(EmailAddress="sender@example.com")
    yield
    ses.delete_identity(Identity="sender@example.com")


@pytest.fixture
def get_fixture_values(request):
    def _get_fixture(fixture):
        return request.getfixturevalue(fixture)

    return _get_fixture
