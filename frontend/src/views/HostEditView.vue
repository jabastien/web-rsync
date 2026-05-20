<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getHost, createHost, updateHost } from "../api/client";
import HostForm from "../components/HostForm.vue";

const route = useRoute();
const router = useRouter();
const hostId = route.params.id ? Number(route.params.id) : null;
const initial = ref<any>(null);
const error = ref("");

onMounted(async () => {
  if (hostId) initial.value = (await getHost(hostId)).data;
});

async function save(data: any) {
  try {
    if (hostId) {
      await updateHost(hostId, data);
    } else {
      await createHost(data);
    }
    router.push("/hosts");
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? e.message;
  }
}
</script>

<template>
  <div class="page">
    <h1 class="page-title">{{ hostId ? "Edit Host" : "New Host" }}</h1>
    <div class="card">
      <p v-if="error" style="color:var(--danger-btn);display:flex;align-items:center;gap:6px">
        <span class="mdi mdi-alert-circle-outline"></span>{{ error }}
      </p>
      <HostForm v-if="!hostId || initial" :initial="initial" @submit="save" />
    </div>
  </div>
</template>
