import random
import os
import boto3
from aws_lambda_powertools import Logger

logger = Logger()


def define_auth_challenge(event):
    session = event["request"]["session"]
    index = len(session) - 1
    response = event["response"]
    challenges = ["SRP_A", "PASSWORD_VERIFIER", "CUSTOM_CHALLENGE"]

    # NOTE: 不正な名称のチャレンジがリクエストされた場合は認証失敗とする。
    if challenges[index] != session[index]["challengeName"]:
        response["issueTokens"] = False
        response["failAuthentication"] = True
        return event

    if (
        index == len(challenges) - 1
        and session[index].get("challengeResult") is True
    ):
        response["issueTokens"] = True
        response["failAuthentication"] = False
    elif (
        index < len(challenges) - 1
        and session[index].get("challengeResult") is True
    ):
        response["issueTokens"] = False
        response["failAuthentication"] = False
        response["challengeName"] = challenges[index + 1]
    else:
        response["issueTokens"] = False
        response["failAuthentication"] = True
    return event


class EmailNotFoundException(Exception):
    pass


class EmailNotDeliveredException(Exception):
    pass


def create_auth_challenge(event):
    ses = boto3.client("ses", endpoint_url=os.getenv("AWS_ENDPOINT_URL"))
    SENDER = os.getenv("SENDER_EMAIL_ADDRESS")
    SUBJECT = "確認コード通知"
    BODY = "こちらのコードでサインインしてください: %s"
    address = event["request"]["userAttributes"].get("email")
    if not address:
        raise EmailNotFoundException
    code = str(random.randint(0, 999999)).zfill(6)
    mail_body = BODY % code

    try:
        response = ses.send_email(
            Destination={"ToAddresses": [address]},
            Message={
                "Body": {"Text": {"Data": mail_body}},
                "Subject": {"Data": SUBJECT},
            },
            Source=SENDER,
        )
        logger.info(response)
    except Exception as e:
        logger.error(e)
        raise EmailNotDeliveredException

    event["response"]["privateChallengeParameters"] = {"code": code}
    return event


def verify_auth_challenge(event):
    code = event["request"]["challengeAnswer"]
    answer = event["request"]["privateChallengeParameters"]["code"]
    event["response"]["answerCorrect"] = code == answer
    return event


@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    HANDLERS = {
        "DefineAuthChallenge": define_auth_challenge,
        "CreateAuthChallenge": create_auth_challenge,
        "VerifyAuthChallengeResponse": verify_auth_challenge,
    }
    trigger_source = event["triggerSource"].split("_")[0]
    handler = HANDLERS.get(trigger_source)
    if not handler:
        logger.error("Invalid Cognito trigger source")
        return
    logger.structure_logs(append=True, handler_name=handler.__name__)
    response = handler(event)
    logger.info(response)
    return response
