import axios from "axios";

const api = axios.create({ baseURL: "/api" });

// ---- Tasks ----
export const getTasks = () => api.get("/tasks");
export const getTask = (id: number) => api.get(`/tasks/${id}`);
export const createTask = (data: object) => api.post("/tasks", data);
export const updateTask = (id: number, data: object) => api.put(`/tasks/${id}`, data);
export const deleteTask = (id: number) => api.delete(`/tasks/${id}`);
export const toggleTask = (id: number, enabled: boolean) =>
  api.patch(`/tasks/${id}/enabled`, null, { params: { enabled } });
export const runTask = (id: number) => api.post(`/tasks/${id}/run`);
export const dryRunTask = (id: number) => api.post(`/tasks/${id}/dry-run`);
export const cloneTask = (id: number) => api.post(`/tasks/${id}/clone`);

// ---- Hosts ----
export const getHosts = () => api.get("/hosts");
export const getHost = (id: number) => api.get(`/hosts/${id}`);
export const createHost = (data: object) => api.post("/hosts", data);
export const updateHost = (id: number, data: object) => api.put(`/hosts/${id}`, data);
export const deleteHost = (id: number) => api.delete(`/hosts/${id}`);
export const getSshKeys = () => api.get("/hosts/ssh-keys");
export const deployKey = (id: number, password: string) =>
  api.post(`/hosts/${id}/deploy-key`, { password });

// ---- Job Runs ----
export const getJobRuns = (params?: object) => api.get("/job-runs", { params });
export const getJobRun = (id: number) => api.get(`/job-runs/${id}`);
export const getJobLog = (id: number) => api.get(`/job-runs/${id}/log`);

// ---- System ----
export const getHealth = () => api.get("/system/health");
export const getSchedulerJobs = () => api.get("/system/scheduler-jobs");
