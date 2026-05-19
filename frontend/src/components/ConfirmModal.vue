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
        <button class="btn-danger" @click="emit('confirm')">{{ confirmLabel ?? "Delete" }}</button>
        <button class="btn-secondary" @click="emit('cancel')">Cancel</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.modal-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  width: 360px;
  box-shadow: 0 8px 32px rgba(0,0,0,.18);
}
.modal-title {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}
.modal-message {
  margin: 0 0 20px;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
}
.modal-actions {
  display: flex;
  gap: 8px;
}
</style>
