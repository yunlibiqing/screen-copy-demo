import Vue from 'vue'
import Router from 'vue-router'
import ScreenCopy from '@/components/ScreenCopy'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'ScreenCopy',
      component: ScreenCopy
    }
  ]
})
