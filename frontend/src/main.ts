import { createApp } from 'vue'
import App from './App.vue'
import router from './app/router'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './app/styles/index.scss'

createApp(App).use(router).use(createPinia()).use(ElementPlus).mount('#app')
