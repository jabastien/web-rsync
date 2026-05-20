import { createApp } from "vue";
import { createPinia } from "pinia";
import "@mdi/font/css/materialdesignicons.min.css";
import App from "./App.vue";
import router from "./router";
import "./style.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
