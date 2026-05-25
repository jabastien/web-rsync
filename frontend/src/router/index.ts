import { createRouter, createWebHistory } from "vue-router";
import Dashboard from "../views/Dashboard.vue";
import TasksView from "../views/TasksView.vue";
import TaskEditView from "../views/TaskEditView.vue";
import HostsView from "../views/HostsView.vue";
import HostEditView from "../views/HostEditView.vue";
import JobHistoryView from "../views/JobHistoryView.vue";
import HelpView from "../views/HelpView.vue";
import NotificationsView from "../views/NotificationsView.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: Dashboard },
    { path: "/tasks", component: TasksView },
    { path: "/tasks/new", component: TaskEditView },
    { path: "/tasks/:id/edit", component: TaskEditView },
    { path: "/hosts", component: HostsView },
    { path: "/hosts/new", component: HostEditView },
    { path: "/hosts/:id/edit", component: HostEditView },
    { path: "/history", component: JobHistoryView },
    { path: "/history/:id", component: JobHistoryView },
    { path: "/notifications", component: NotificationsView },
    { path: "/help", component: HelpView },
  ],
});
