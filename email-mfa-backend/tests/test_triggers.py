import pytest
from unittest import mock
import re
import boto3
from botocore.stub import Stubber
from functions.triggers import app


class TestDefineAuthChallenge:
    @pytest.fixture
    def event(self):
        return {
            "version": "1",
            "region": "ap-northeast-1",
            "userPoolId": "ap-northeast-1_OFrFlFQQt",
            "userName": "6d82908b-7199-4ec2-8ea1-ef0961ae12a4",
            "callerContext": {
                "awsSdkVersion": "aws-sdk-unknown-unknown",
                "clientId": "5j22n49ha1o0rj6eurpjs2gp5p",
            },
            "request": {
                "userAttributes": {
                    "sub": "6d82908b-7199-4ec2-8ea1-ef0961ae12a4",
                    "email_verified": "true",
                    "cognito:user_status": "CONFIRMED",
                    "email": "user1@example.com",
                },
                "userNotFound": False,
            },
            "triggerSource": "DefineAuthChallenge_Authentication",
            "response": {
                "challengeName": None,
                "issueTokens": None,
                "failAuthentication": None,
            },
        }

    @pytest.fixture
    def srp_a_event(self, event):
        event["request"]["session"] = [
            {
                "challengeName": "SRP_A",
                "challengeResult": True,
                "challengeMetadata": None,
            }
        ]
        return event

    @pytest.fixture
    def password_verifier_event(self, event):
        event["request"]["session"] = [
            {
                "challengeName": "SRP_A",
                "challengeResult": True,
                "challengeMetadata": None,
            },
            {
                "challengeName": "PASSWORD_VERIFIER",
                "challengeResult": True,
                "challengeMetadata": None,
            },
        ]
        return event

    @pytest.fixture
    def custom_challenge_event(self, event):
        event["request"]["session"] = [
            {
                "challengeName": "SRP_A",
                "challengeResult": True,
                "challengeMetadata": None,
            },
            {
                "challengeName": "PASSWORD_VERIFIER",
                "challengeResult": True,
                "challengeMetadata": None,
            },
            {
                "challengeName": "CUSTOM_CHALLENGE",
                "challengeResult": True,
                "challengeMetadata": None,
            },
        ]
        return event

    def test_1st_challenge(self, srp_a_event, lambda_context):
        result = app.lambda_handler(srp_a_event, lambda_context)
        assert result["response"]["issueTokens"] is False
        assert result["response"]["failAuthentication"] is False
        assert result["response"]["challengeName"] == "PASSWORD_VERIFIER"

    def test_2nd_challenge(self, password_verifier_event, lambda_context):
        result = app.lambda_handler(password_verifier_event, lambda_context)
        assert result["response"]["issueTokens"] is False
        assert result["response"]["failAuthentication"] is False
        assert result["response"]["challengeName"] == "CUSTOM_CHALLENGE"

    def test_3rd_challenge(self, custom_challenge_event, lambda_context):
        result = app.lambda_handler(custom_challenge_event, lambda_context)
        assert result["response"]["issueTokens"] is True
        assert result["response"]["failAuthentication"] is False

    def test_invalid_challenge_name(self, event, lambda_context):
        event["request"]["session"] = [
            {
                "challengeName": "HOGE",
                "challengeResult": True,
                "challengeMetadata": None,
            }
        ]
        result = app.lambda_handler(event, lambda_context)
        assert result["response"]["failAuthentication"] is True

    @pytest.mark.parametrize(
        "event_name",
        ["srp_a_event", "password_verifier_event", "custom_challenge_event"],
    )
    def test_fail_challenge(
        self, event_name, lambda_context, get_fixture_values
    ):
        event = get_fixture_values(event_name)
        event["request"]["session"][-1]["challengeResult"] = False
        result = app.lambda_handler(event, lambda_context)
        assert result["response"]["issueTokens"] is False
        assert result["response"]["failAuthentication"] is True


class TestCreateAuthChallenge:
    @pytest.fixture
    def event(self):
        return {
            "version": "1",
            "region": "ap-northeast-1",
            "userPoolId": "ap-northeast-1_OFrFlFQQt",
            "userName": "6d82908b-7199-4ec2-8ea1-ef0961ae12a4",
            "callerContext": {
                "awsSdkVersion": "aws-sdk-unknown-unknown",
                "clientId": "5j22n49ha1o0rj6eurpjs2gp5p",
            },
            "triggerSource": "CreateAuthChallenge_Authentication",
            "request": {
                "userAttributes": {
                    "sub": "6d82908b-7199-4ec2-8ea1-ef0961ae12a4",
                    "email_verified": "true",
                    "cognito:user_status": "CONFIRMED",
                    "email": "user1@example.com",
                },
                "challengeName": "CUSTOM_CHALLENGE",
                "session": [
                    {
                        "challengeName": "SRP_A",
                        "challengeResult": True,
                        "challengeMetadata": None,
                    },
                    {
                        "challengeName": "PASSWORD_VERIFIER",
                        "challengeResult": True,
                        "challengeMetadata": None,
                    },
                ],
                "userNotFound": False,
            },
            "response": {
                "publicChallengeParameters": None,
                "privateChallengeParameters": None,
                "challengeMetadata": None,
            },
        }

    def test_create_challenge(self, event, lambda_context):
        result = app.lambda_handler(event, lambda_context)
        code = result["response"]["privateChallengeParameters"].get("code")
        assert code is not None
        assert re.match(r"^[0-9]{6}$", code) is not None

    def test_email_not_found(self, event, lambda_context):
        event["request"]["userAttributes"].pop("email")
        with pytest.raises(app.EmailNotFoundException):
            app.lambda_handler(event, lambda_context)

    def test_email_not_delivered(self, event, lambda_context):
        client = boto3.client("ses")
        stubber = Stubber(client)
        stubber.add_client_error(
            "send_email", service_error_code="MessageRejected"
        )
        with stubber:
            with mock.patch(
                "boto3.client", mock.MagicMock(return_value=client)
            ):
                with pytest.raises(app.EmailNotDeliveredException):
                    app.lambda_handler(event, lambda_context)


class TestVerifyAuthChallengeResponse:
    @pytest.fixture
    def event(self):
        return {
            "version": "1",
            "region": "ap-northeast-1",
            "userPoolId": "ap-northeast-1_OFrFlFQQt",
            "userName": "6d82908b-7199-4ec2-8ea1-ef0961ae12a4",
            "callerContext": {
                "awsSdkVersion": "aws-sdk-unknown-unknown",
                "clientId": "5j22n49ha1o0rj6eurpjs2gp5p",
            },
            "triggerSource": "VerifyAuthChallengeResponse_Authentication",
            "request": {
                "userAttributes": {
                    "sub": "6d82908b-7199-4ec2-8ea1-ef0961ae12a4",
                    "email_verified": "true",
                    "cognito:user_status": "CONFIRMED",
                    "email": "user1@example.com",
                },
                "privateChallengeParameters": {"code": "012345"},
                "challengeAnswer": "012345",
                "userNotFound": False,
            },
            "response": {"answerCorrect": None},
        }

    def test_custom_challenge_success(self, event, lambda_context):
        result = app.lambda_handler(event, lambda_context)
        assert result["response"]["answerCorrect"] is True

    def test_custom_challenge_fail(self, event, lambda_context):
        event["request"]["challengeAnswer"] = "987654"
        result = app.lambda_handler(event, lambda_context)
        assert result["response"]["answerCorrect"] is False
