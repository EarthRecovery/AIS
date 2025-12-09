<template>
  <div class="page">
    <div class="upper">
        aaa
    </div>
    <div class="history">
        <div class="history_header">历史记录</div>
        <n-scrollbar style="height: 100%;">
            bbb
            <br><br><br><br><br><br><br>
            <br><br><br><br><br><br><br>
            <br><br><br><br><br><br><br>
            <br><br><br><br><br><br><br>
            <br><br><br><br><br><br><br>
            <br><br><br><br><br><br><br>
            ... 内容很多 ...
        </n-scrollbar>
    </div>
  </div>
</template>

<script setup>
import { NScrollbar } from 'naive-ui'
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
}
.upper {
  flex: 0 0 30%;
}
.history {
  flex: 0 0 70%;
  overflow: hidden;
}
.history_header {
  height: 40px;
  line-height: 40px;
  text-align: center;
  font-weight: bold;
  font-size: 20px;
  /* border-bottom: 1px solid #ccc; */
}
</style>