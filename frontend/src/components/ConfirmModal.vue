<script setup lang="ts">
defineProps<{
  title: string;
  message: string;
  confirmLabel?: string;
}>();
const emit = defineEmits<{
  (e: "confirm"): void;
  (e: "cancel"): void;
}>();
</script>

<template>
  <div class="modal-overlay" @click.self="emit('cancel')">
    <div class="modal-card">
      <h3 class="modal-title">{{ title }}</h3>
      <p class="modal-message">{{ message }}</p>
      <div class="modal-actions">
        <button class="btn-danger" @click="emit('confirm')">
          <span class="mdi mdi-check"></span>{{ confirmLabel ?? "Delete" }}
        </button>
        <button class="btn-secondary" @click="emit('cancel')">
          <span class="mdi mdi-close"></span>Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--modal-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 16px;
}

.modal-card {
  background: var(--modal-bg);
  border-radius: 10px;
  padding: 24px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 8px 40px rgba(0,0,0,.4);
}

.modal-title {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-strong);
}

.modal-message {
  margin: 0 0 20px;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
}

.modal-actions {
  display: flex;
  gap: 8px;
}
</style>
