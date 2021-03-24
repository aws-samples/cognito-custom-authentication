const settings = {

  Auth: {
    region: process.env.VUE_APP_AWS_REGION, // Cognito UserPoolのリージョン
    userPoolId: process.env.VUE_APP_USER_POOL_ID, // Cognito UserPool ID
    userPoolWebClientId: process.env.VUE_APP_USER_WEB_CLIENT_ID // Cognito UserPool のアプリクライアントID
  }
}

export default settings
