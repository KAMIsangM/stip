<template>
  <div class="auth-scene">
    <!-- soft gradient orbs -->
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>

    <!-- subtle grid pattern -->
    <div class="grid-bg"></div>

    <!-- main layout -->
    <div class="auth-layout">
      <!-- decorative panel -->
      <div class="decor-panel">
        <div class="decor-inner">
          <div class="decor-logo">
            <svg viewBox="0 0 48 48" fill="none" class="logo-svg">
              <rect width="48" height="48" rx="14" fill="url(#logo-grad)" />
              <path d="M16 32V18L24 26L32 18V32" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
              <defs>
                <linearGradient id="logo-grad" x1="0" y1="0" x2="48" y2="48">
                  <stop stop-color="#3b82f6" />
                  <stop offset="1" stop-color="#06b6d4" />
                </linearGradient>
              </defs>
            </svg>
            <h1 class="logo-text">SITP</h1>
          </div>
          <p class="decor-title">智能互动教学平台</p>
          <p class="decor-desc">AI 驱动的下一代学习体验，让知识获取更高效</p>

          <div class="decor-features">
            <div class="feat-item">
              <div class="feat-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" stroke="#3b82f6" stroke-width="1.2" />
                  <path d="M5 8l2 2 4-4" stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </div>
              <span>AI 知识建模与图谱</span>
            </div>
            <div class="feat-item">
              <div class="feat-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" stroke="#06b6d4" stroke-width="1.2" />
                  <path d="M5 8l2 2 4-4" stroke="#06b6d4" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </div>
              <span>智能课件自动生成</span>
            </div>
            <div class="feat-item">
              <div class="feat-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" stroke="#8b5cf6" stroke-width="1.2" />
                  <path d="M5 8l2 2 4-4" stroke="#8b5cf6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </div>
              <span>互动学习与测验</span>
            </div>
            <div class="feat-item">
              <div class="feat-icon">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <circle cx="8" cy="8" r="7" stroke="#f59e0b" stroke-width="1.2" />
                  <path d="M5 8l2 2 4-4" stroke="#f59e0b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </div>
              <span>语音讲解与 PPT</span>
            </div>
          </div>
        </div>
      </div>

      <!-- form panel -->
      <div class="form-panel">
        <div class="form-card">
          <div class="form-header">
            <h2 class="form-title">欢迎回来 👋</h2>
            <p class="form-sub">登录你的账户继续学习</p>
          </div>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            class="auth-form"
            @submit.prevent="handleLogin"
          >
            <el-form-item prop="email">
              <el-input
                v-model="form.email"
                placeholder="请输入邮箱地址"
                size="large"
                class="custom-input"
              >
                <template #prefix>
                  <el-icon class="input-icon"><Message /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                show-password
                class="custom-input"
                @keyup.enter="handleLogin"
              >
                <template #prefix>
                  <el-icon class="input-icon"><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item>
              <el-button
                native-type="submit"
                size="large"
                :loading="authStore.loading"
                class="submit-btn"
                round
              >
                登 录
              </el-button>
            </el-form-item>
          </el-form>

          <div class="form-footer">
            <span class="footer-text">还没有账户？</span>
            <router-link to="/register" class="footer-link">
              立即注册 <span class="arrow">→</span>
            </router-link>
          </div>

          <div class="test-hint">
            <div class="test-label">测试账户</div>
            <div class="test-value">
              <code>demo@sitp.local</code>
              <span>/</span>
              <code>demo123</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Message, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()

const form = reactive({
  email: '',
  password: '',
})

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

async function handleLogin() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await authStore.login(form.email, form.password)
      ElMessage.success('登录成功')
      const redirect = (route.query.redirect as string) || '/'
      router.push(redirect)
    } catch (err: any) {
      const detail = err?.response?.data?.detail || '登录失败，请检查邮箱和密码'
      ElMessage.error(detail)
    }
  })
}
</script>

<style scoped>
.auth-scene {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f4ff;
  position: relative;
  overflow: hidden;
}

/* ===== animated gradient orbs ===== */
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  pointer-events: none;
}
.orb-1 {
  width: 560px; height: 560px;
  background: rgba(59,130,246,0.10);
  top: -180px; right: -120px;
  animation: orbA 16s ease-in-out infinite;
}
.orb-2 {
  width: 440px; height: 440px;
  background: rgba(6,182,212,0.08);
  bottom: -140px; left: -100px;
  animation: orbB 20s ease-in-out infinite 3s;
}
.orb-3 {
  width: 360px; height: 360px;
  background: rgba(139,92,246,0.06);
  top: 50%; left: 55%;
  animation: orbC 18s ease-in-out infinite 6s;
}
@keyframes orbA {
  0%,100% { transform: translate(0,0) scale(1); }
  33% { transform: translate(-40px,30px) scale(1.08); }
  66% { transform: translate(25px,-15px) scale(0.94); }
}
@keyframes orbB {
  0%,100% { transform: translate(0,0) scale(1); }
  33% { transform: translate(35px,-25px) scale(1.10); }
  66% { transform: translate(-20px,15px) scale(0.92); }
}
@keyframes orbC {
  0%,100% { transform: translate(0,0) scale(1); }
  33% { transform: translate(-25px,-30px) scale(1.06); }
  66% { transform: translate(30px,20px) scale(0.96); }
}

/* ===== subtle grid ===== */
.grid-bg {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(59,130,246,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59,130,246,0.03) 1px, transparent 1px);
  background-size: 64px 64px;
  pointer-events: none;
  mask-image: radial-gradient(ellipse at center, black 20%, transparent 70%);
}

/* ===== main layout ===== */
.auth-layout {
  position: relative; z-index: 1;
  display: flex;
  width: 100%; max-width: 960px; min-height: 560px;
  border-radius: 24px;
  overflow: hidden;
  background: #fff;
  box-shadow:
    0 1px 3px rgba(0,0,0,0.04),
    0 8px 40px rgba(0,0,0,0.06),
    0 20px 80px rgba(59,130,246,0.06);
  animation: cardEnter 0.7s cubic-bezier(0.16,1,0.3,1);
}
@keyframes cardEnter {
  from { opacity: 0; transform: translateY(20px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* ===== decorative panel ===== */
.decor-panel {
  flex: 0 0 44%;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(160deg, #eff6ff 0%, #ecfeff 50%, #f5f3ff 100%);
  position: relative; overflow: hidden;
}
.decor-panel::before {
  content: '';
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse at 20% 80%, rgba(59,130,246,0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(6,182,212,0.06) 0%, transparent 50%);
}
.decor-inner {
  position: relative; z-index: 1;
  padding: 48px 40px;
}
.decor-logo {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 20px;
}
.logo-svg {
  width: 44px; height: 44px;
  filter: drop-shadow(0 4px 12px rgba(59,130,246,0.2));
}
.logo-text {
  font-size: 30px; font-weight: 800;
  color: #1e293b;
  letter-spacing: 0.04em; margin: 0; line-height: 1;
}
.decor-title {
  font-size: 17px; font-weight: 600;
  color: #334155; margin: 0 0 6px;
}
.decor-desc {
  font-size: 13px; color: #94a3b8;
  margin: 0 0 36px; line-height: 1.6;
}
.decor-features {
  display: flex; flex-direction: column; gap: 14px;
}
.feat-item {
  display: flex; align-items: center; gap: 11px;
  font-size: 14px; color: #475569;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255,255,255,0.6);
  transition: background 0.2s;
}
.feat-item:hover {
  background: rgba(255,255,255,0.9);
}
.feat-icon {
  flex-shrink: 0; display: flex;
}

/* ===== form panel ===== */
.form-panel {
  flex: 0 0 56%;
  display: flex; align-items: center; justify-content: center;
  padding: 48px;
}
.form-card {
  width: 100%; max-width: 380px;
}
.form-header {
  margin-bottom: 32px;
}
.form-title {
  font-size: 26px; font-weight: 700;
  color: #1e293b; margin: 0 0 6px;
}
.form-sub {
  font-size: 14px; color: #94a3b8; margin: 0;
}

/* ===== inputs ===== */
.auth-form :deep(.el-form-item) {
  margin-bottom: 18px;
}
.auth-form :deep(.el-form-item__error) {
  font-size: 12px; padding-top: 4px; color: #ef4444;
}

.custom-input :deep(.el-input__wrapper) {
  background: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
  padding: 2px 14px;
  transition: all 0.25s cubic-bezier(0.16,1,0.3,1);
}
.custom-input :deep(.el-input__wrapper:hover) {
  border-color: #93c5fd !important;
  background: #ffffff !important;
  box-shadow: 0 2px 4px rgba(59,130,246,0.04) !important;
}
.custom-input :deep(.el-input__wrapper.is-focus) {
  border-color: #3b82f6 !important;
  background: #ffffff !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.08), 0 2px 8px rgba(59,130,246,0.06) !important;
}
.custom-input :deep(.el-input__inner) {
  font-size: 14px; color: #1e293b;
  height: 44px; line-height: 44px;
  background: transparent !important;
}
.custom-input :deep(.el-input__inner::placeholder) {
  color: #cbd5e1;
}
/* 覆盖浏览器自动填充的默认背景色 */
.custom-input :deep(.el-input__inner:-webkit-autofill),
.custom-input :deep(.el-input__inner:-webkit-autofill:hover),
.custom-input :deep(.el-input__inner:-webkit-autofill:focus) {
  -webkit-box-shadow: 0 0 0 1000px #ffffff inset !important;
  -webkit-text-fill-color: #1e293b !important;
  transition: background-color 5000s ease-in-out 0s;
}
.custom-input :deep(.el-input__suffix) {
  color: #94a3b8;
}
/* 自动填充时也保持wrapper白色 */
.custom-input :deep(.el-input__wrapper:has(.el-input__inner:-webkit-autofill)) {
  background: #ffffff !important;
}

.input-icon {
  font-size: 17px; color: #94a3b8;
  transition: color 0.25s;
}
.custom-input:focus-within .input-icon {
  color: #3b82f6;
}

/* ===== button ===== */
.submit-btn {
  width: 100% !important;
  height: 48px !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  letter-spacing: 0.06em;
  border: none !important;
  margin-top: 4px;
  background: linear-gradient(135deg, #3b82f6, #6366f1) !important;
  color: #fff !important;
  transition: all 0.3s cubic-bezier(0.16,1,0.3,1);
}
.submit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 28px rgba(59,130,246,0.35);
  background: linear-gradient(135deg, #60a5fa, #818cf8) !important;
}
.submit-btn:active {
  transform: translateY(0);
}

/* ===== footer ===== */
.form-footer {
  display: flex; align-items: center; justify-content: center;
  gap: 6px; margin-top: 20px;
}
.footer-text {
  font-size: 14px; color: #94a3b8;
}
.footer-link {
  font-size: 14px; font-weight: 500;
  color: #3b82f6; text-decoration: none;
  transition: color 0.2s;
}
.footer-link:hover { color: #2563eb; }
.arrow {
  display: inline-block;
  transition: transform 0.2s;
}
.footer-link:hover .arrow { transform: translateX(3px); }

/* ===== test hint ===== */
.test-hint {
  display: flex; align-items: center; gap: 12px;
  margin-top: 24px;
  padding: 12px 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}
.test-label {
  flex-shrink: 0;
  font-size: 11px; font-weight: 600;
  color: #3b82f6;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(59,130,246,0.08);
}
.test-value {
  display: flex; align-items: center; gap: 5px;
  overflow: hidden;
}
.test-value code {
  font-size: 12px;
  font-family: 'SF Mono','Fira Code','Consolas',monospace;
  color: #64748b; white-space: nowrap;
}
.test-value span { color: #cbd5e1; }

/* ===== responsive ===== */
@media (max-width: 800px) {
  .auth-layout {
    max-width: 420px; flex-direction: column; min-height: auto;
  }
  .decor-panel {
    flex: none;
    border-bottom: 1px solid #e2e8f0;
  }
  .decor-inner {
    padding: 28px 28px 20px; text-align: center;
  }
  .decor-logo { justify-content: center; }
  .decor-desc { margin-bottom: 20px; }
  .form-panel {
    flex: none; padding: 32px 28px;
  }
  .form-header { text-align: center; }
}
@media (max-width: 440px) {
  .decor-inner { padding: 24px 20px 18px; }
  .form-panel { padding: 28px 20px; }
  .logo-svg { width: 36px; height: 36px; }
  .logo-text { font-size: 24px; }
}
</style>
