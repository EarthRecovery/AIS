<template>
  <div class="auth-page">
    <n-card size="huge" class="auth-card" :bordered="false">
      <div class="title">Persona Chat</div>
      <div class="tabs">
        <n-button :type="isLogin ? 'primary' : 'default'" quaternary class="tab-btn" @click="isLogin = true">登录</n-button>
        <n-button :type="!isLogin ? 'primary' : 'default'" quaternary class="tab-btn" @click="isLogin = false">注册</n-button>
      </div>
      <n-form :model="form" :rules="rules" ref="formRef" label-placement="top">
        <n-form-item v-if="!isLogin" label="昵称" path="name">
          <n-input v-model:value="form.name" placeholder="请输入昵称" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="form.email" placeholder="请输入邮箱（可选）" />
        </n-form-item>
        <n-form-item label="手机号" path="phone_number">
          <n-input v-model:value="form.phone_number" placeholder="请输入手机号（可选）" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="form.password" type="password" show-password-on="click" placeholder="请输入密码" />
        </n-form-item>
        <n-space justify="space-between" align="center">
          <n-button tertiary class="link-btn" @click="toggleMode">{{ isLogin ? '去注册' : '去登录' }}</n-button>
          <n-button type="primary" :loading="loading" @click="handleSubmit">
            {{ isLogin ? '登录' : '注册' }}
          </n-button>
        </n-space>
      </n-form>
    </n-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const router = useRouter()
const message = useMessage()
const isLogin = ref(true)
const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  name: '',
  email: '',
  phone_number: '',
  password: '',
})

const rules = {
  name: [{ required: () => !isLogin.value, message: '请输入昵称' }],
  email: [{ type: 'email', message: '邮箱格式不正确' }],
  phone_number: [],
  password: [{ required: true, message: '请输入密码' }],
  contact: [
    {
      validator: () => {
        if (!form.email && !form.phone_number) {
          return new Error('请输入邮箱或手机号')
        }
        return true
      },
      trigger: ['blur', 'input'],
    },
  ],
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
}

const handleSubmit = async () => {
  loading.value = true
  try {
    if (!form.email && !form.phone_number) {
      throw new Error('请输入邮箱或手机号')
    }
    await formRef.value?.validate()
    if (isLogin.value) {
      await auth.login({
        email: form.email,
        phone_number: form.phone_number,
        password: form.password,
      })
      message.success('登录成功')
      router.replace('/app')
    } else {
      await auth.register({
        name: form.name,
        email: form.email,
        phone_number: form.phone_number || undefined,
        password: form.password,
      })
      message.success('注册成功，请登录')
      isLogin.value = true
    }
  } catch (err) {
    const detail = err?.response?.data?.detail || err?.message || '操作失败'
    message.error(detail)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

:deep(.n-card) {
  font-family: 'Space Grotesk', 'Poppins', 'Inter', system-ui, -apple-system, sans-serif;
}

.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 25% 20%, #1b1f3a, #0b0c14 40%), radial-gradient(circle at 80% 0%, #20456f, #0b0c14 38%), linear-gradient(135deg, #0a0c12 0%, #0f172a 100%);
  color: #f8fafc;
}

.auth-card {
  width: 440px;
  background: #0f172a;
  color: #e2e8f0;
  box-shadow: 0 18px 70px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(255, 255, 255, 0.05);
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.title {
  font-size: 26px;
  letter-spacing: 0.2px;
  font-weight: 700;
  margin-bottom: 16px;
  text-align: center;
}

.tabs {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-bottom: 12px;
}

/* 调整 tabs 与切换按钮的文字色 */
:deep(.n-button.quaternary-type) {
  color: #cbd5e1;
}
:deep(.n-button.quaternary-type:hover) {
  color: #e2e8f0;
}

n-form-item {
  color: rgb(175, 22, 22);
}

:deep(.n-form-item-label) {
  color: #cbd5e1;
  font-weight: 600;
}

:deep(.n-input__input),
:deep(.n-input__textarea-el) {
  color: #f8fafc;
}

:deep(.n-input__input::placeholder),
:deep(.n-input__textarea-el::placeholder) {
  color: #94a3b8;
}

.tab-btn {
  color: #cbd5e1;
}
.tab-btn:hover {
  color: #e2e8f0;
}

.link-btn {
  color: #cbd5e1;
}
.link-btn:hover {
  color: #e2e8f0;
}
</style>
