<template>
  <div id="app">
    <el-container>
      <el-header>Custom Auth Flow</el-header>
      <el-main>
        <el-form>
          <div v-if="signInState === 'newPassword'">
            <el-form-item label="New Password">
              <el-input type="password" v-model="newpassword"></el-input>
            </el-form-item>
            <el-button @click="changePassword" >ChangePassword</el-button>
          </div>
          <div v-else-if="signInState === 'customChallenge'">
            <el-form-item label="EMail MFA Value">
              <el-input type="password" v-model="customanswer"></el-input>
            </el-form-item>
            <el-button @click="onetime" >OneTimePassword</el-button>
          </div>
          <div v-else-if="signInState === 'signedIn'">
            Signed in.<br>
            <el-button @click="signOut">SignOut</el-button>
          </div>
          <div v-else>
            <el-form-item label="User Name">
              <el-input type="text" v-model="username"></el-input>
            </el-form-item>
            <el-form-item label="Password">
              <el-input type="password" v-model="password"></el-input>
            </el-form-item>
            <el-button @click="startSignIn" >SignIn</el-button>
          </div>
        </el-form>
      </el-main>
    </el-container>
  </div>
</template>
<script>
import { Auth } from 'aws-amplify'
import { AmplifyEventBus } from 'aws-amplify-vue'
Auth.configure({
  authenticationFlowType: 'CUSTOM_AUTH'
})
export default {
  name: 'app',
  data () {
    return {
      signInState: '',
      username: '',
      password: '',
      newpassword: '',
      customanswer: '',
      challenge: {}
    }
  },
  methods: {
    async processSignIn () {
      if (await this.isSignedIn()) {
        this.signInState = 'signedIn'
        return
      }
      switch (this.challenge.challengeName) {
        case 'NEW_PASSWORD_REQUIRED':
          this.signInState = 'newPassword'
          break
        case 'CUSTOM_CHALLENGE':
          this.signInState = 'customChallenge'
          break
        default:
          throw Exception('Unknown challenge; something is wrong') /* global Exception */
      }
    },
    async onetime () {
      try {
        this.challenge = await Auth.sendCustomChallengeAnswer(this.challenge, this.customanswer)
        this.processSignIn()
      } catch (err) {
        this.$message.error({
          message: 'Code is wrong..',
          showClose: true
        })
        this.signInState = ''
      }
    },
    async signOut () {
      await Auth.signOut()
      this.signInState = ''
    },
    async changePassword () {
      try {
        this.challenge = await Auth.completeNewPassword(this.challenge, this.newpassword)
        this.processSignIn()
      } catch (err) {
        this.$message.error({
          message: err.message,
          showClose: true
        })
        this.signInState = ''
      }
    },
    async startSignIn () {
      try {
        this.challenge = await Auth.signIn(this.username, this.password)
        this.processSignIn()
      } catch (err) {
        this.$message.error({
          message: err.message,
          showClose: true
        })
        this.signInState = ''
      }
    },
    async isSignedIn () {
      try {
        await Auth.currentAuthenticatedUser()
        return true
      } catch (err) {
        return false
      }
    }
  },
  async created () {
    if (await this.isSignedIn()) {
      this.signInState = 'signedIn'
    }
    AmplifyEventBus.$on('authState', async info => {
      if (await this.isSignedIn()) {
        this.signInState = 'signedIn'
      }
    })
  }
}

</script>
