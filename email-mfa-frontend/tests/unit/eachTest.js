import Vue from 'vue'
import ElementUI from 'element-ui'
import locale from 'element-ui/lib/locale/lang/ja'
import Amplify, * as AmplifyModules from 'aws-amplify'
import { AmplifyPlugin } from 'aws-amplify-vue'

// Amplify Test config
Amplify.configure({
  Auth: {
    region: 'ap-northeast-1', // Cognito UserPool region
    userPoolId: 'ap-northeast-1_TEST_TEST', // Cognito UserPool ID
    userPoolWebClientId: 'TEST_TEST' // Cognito UserPool client ID
  }
})
Vue.use(AmplifyPlugin, AmplifyModules)
Vue.use(ElementUI, { locale })
