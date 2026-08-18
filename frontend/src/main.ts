import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { setConfig, frappeRequest } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import { useSessionStore } from '@/stores/session'
import './style.css'

// frappe-ui's createResource/createListResource fall back to a bare fetch()
// unless a resourceFetcher is configured -- without this, calls 404 because
// they resolve against the SPA route instead of /api/method/.
setConfig('resourceFetcher', frappeRequest)

const app = createApp(App)
app.use(createPinia())
useSessionStore().bootstrap()
app.use(router)
app.mount('#pp2-hotel-app')
