<template>
  <div class="page">
    <div class="panel panel--left">
      <dashboard />
    </div>
    <div class="panel panel--right">
      <chat />
    </div>
  </div>
</template>

<script setup>
import Dashboard from '@/components/DashBoard.vue'
import Chat from '@/components/Chat.vue'

</script>

<style scoped>
.page {
  display: flex;
  width: 100%;
  height: 100vh;
  font-family: 'Poppins', sans-serif;
}

.panel {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.panel--left {
  flex: 0 0 20%;
  background-color: #262626;
  color: rgb(203, 203, 203);
}

.panel--right {
  flex: 0 0 80%;
  background-color: #d5d5d5;
  color: #232323;
}
</style>
