<template>
  <div class="shell">
    <AppNav />
    <div class="page">
      <div class="panel panel--left">
        <dashboard />
      </div>
      <div class="panel panel--right">
        <chat />
      </div>
    </div>
  </div>
</template>

<script setup>
import AppNav from '@/components/AppNav.vue'
import Dashboard from '@/components/DashBoard.vue'
import Chat from '@/components/Chat.vue'

</script>

<style scoped>
.shell {
  display: flex;
  flex-direction: column;
  height: 100vh;
  font-family: 'Poppins', sans-serif;
}
.page {
  display: flex;
  flex: 1;
  width: 100%;
  min-height: 0;
}

.panel {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.panel--left {
  flex: 0 0 20%;
  background-color: #414141;
  color: rgb(203, 203, 203);
}

.panel--right {
  flex: 0 0 80%;
  background-color: #d5d5d5;
  color: #232323;
}
</style>
