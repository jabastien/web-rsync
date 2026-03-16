<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getTask, createTask, updateTask } from "../api/client";
import TaskForm from "../components/TaskForm.vue";

const route = useRoute();
const router = useRouter();
const taskId = route.params.id ? Number(route.params.id) : null;
const initial = ref<any>(null);
const error = ref("");

onMounted(async () => {
  if (taskId) {
    initial.value = (await getTask(taskId)).data;
  }
});

async function save(data: any) {
  try {
    if (taskId) {
      await updateTask(taskId, data);
    } else {
      await createTask(data);
    }
    router.push("/tasks");
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? e.message;
  }
}
</script>

<template>
  <div class="page">
    <h1 class="page-title">{{ taskId ? "Edit Task" : "New Task" }}</h1>
    <div class="card">
      <p v-if="error" style="color:red">{{ error }}</p>
      <TaskForm v-if="!taskId || initial" :initial="initial" @submit="save" />
    </div>
  </div>
</template>
