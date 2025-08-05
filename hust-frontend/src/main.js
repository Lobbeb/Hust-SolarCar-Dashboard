import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import { useTelemStore } from "./store.js";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);

// Make store available globally for error handling
const store = useTelemStore();
app.provide('telemStore', store);

app.mount("#app");

// Initialize store after mounting
store.init().catch(error => {
  console.error("Failed to initialize application:", error);
});
