import Vue from 'vue'
import App from './App.vue'
import awsconfig from './aws-exports'
import Amplify, * as AmplifyModules from 'aws-amplify'
import { AmplifyPlugin } from 'aws-amplify-vue'
import 'element-ui/lib/theme-chalk/index.css'
import locale from 'element-ui/lib/locale/lang/ja'
import ElementUI from 'element-ui'

Amplify.configure(awsconfig)
Vue.config.productionTip = false

Vue.use(AmplifyPlugin, AmplifyModules)
Vue.use(ElementUI, { locale })
new Vue({
  render: h => h(App)
}).$mount('#app')
