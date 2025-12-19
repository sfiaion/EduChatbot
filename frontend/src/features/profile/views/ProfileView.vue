<template>
  <div class="profile-container">
    <div class="glass-card">
      <div class="header">
        <h2>个人资料</h2>
        <p>管理您的个人信息</p>
      </div>

      <div class="profile-content" v-if="form">
        <div class="avatar-section">
          <el-avatar :size="100" :src="form.avatar || defaultAvatar" class="avatar-img" />
          <div class="avatar-edit">
             <el-upload
                class="avatar-uploader"
                action="#"
                :show-file-list="false"
                :http-request="handleUpload"
                :before-upload="beforeUpload"
              >
                <el-button type="primary" size="small">更换头像</el-button>
              </el-upload>
          </div>
        </div>

        <el-form :model="form" label-position="top" class="profile-form" size="large">
          <div class="form-grid">
            <el-form-item label="昵称">
              <el-input v-model="form.nickname" placeholder="设置您的昵称" />
            </el-form-item>
            
            <el-form-item label="真实姓名 (不可修改)">
               <el-input v-model="form.name" disabled />
            </el-form-item>

            <el-form-item label="用户名 (不可修改)">
               <el-input v-model="form.username" disabled />
            </el-form-item>
            
            <el-form-item label="角色">
               <el-tag :type="form.role === 'admin' ? 'danger' : 'primary'">{{ form.role }}</el-tag>
            </el-form-item>

            <el-form-item label="班级" v-if="form.role === 'student' && form.className">
               <el-input v-model="form.className" disabled />
            </el-form-item>

            <el-form-item label="班主任/老师" v-if="form.role === 'student' && form.teacherName">
               <el-input v-model="form.teacherName" disabled />
            </el-form-item>

             <el-form-item label="负责班级" v-if="form.role === 'teacher' && form.classes && form.classes.length">
               <el-tag v-for="c in form.classes" :key="c" style="margin-right:8px;">{{ c }}</el-tag>
            </el-form-item>

            <el-form-item label="手机号">
              <el-input v-model="form.phone" placeholder="绑定手机号" />
            </el-form-item>

            <el-form-item label="邮箱">
              <el-input v-model="form.email" placeholder="绑定邮箱" />
            </el-form-item>
          </div>

          <div class="actions">
            <el-button type="danger" plain @click="handleLogout" class="save-btn" style="margin-right: 12px;">
               退出登录
            </el-button>
            <el-button type="primary" @click="saveProfile" :loading="loading" class="save-btn">
              保存修改
            </el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useAuthStore } from '../../../stores/auth'
import { ElMessage, type UploadRequestOptions } from 'element-plus'
import { api } from '../../../services/apiClient'

import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const loading = ref(false)
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'

const form = reactive({
  username: '',
  name: '',
  nickname: '',
  phone: '',
  email: '',
  avatar: '',
  role: '',
  className: '',
  teacherName: '',
  classes: [] as string[]
})

async function handleUpload(options: UploadRequestOptions) {
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    const res = await api.post('/api/upload/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    form.avatar = res.data.url
    ElMessage.success('头像上传成功')
  } catch (error) {
    ElMessage.error('上传失败')
  }
}

function beforeUpload(rawFile: File) {
  if (rawFile.type !== 'image/jpeg' && rawFile.type !== 'image/png') {
    ElMessage.error('Avatar picture must be JPG format!')
    return false
  } else if (rawFile.size / 1024 / 1024 > 2) {
    ElMessage.error('Avatar picture size can not exceed 2MB!')
    return false
  }
  return true
}

onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchMe()
  }
  if (authStore.user) {
    Object.assign(form, {
        username: authStore.user.username,
        name: authStore.user.name,
        nickname: authStore.user.nickname || '',
        phone: authStore.user.phone || '',
        email: authStore.user.email || '',
        avatar: authStore.user.avatar || '',
        role: authStore.user.role,
        className: (authStore.user as any).class_name || '',
        teacherName: (authStore.user as any).teacher_name || '',
        classes: (authStore.user as any).classes || []
    })
  }
})

async function saveProfile() {
  loading.value = true
  try {
    await authStore.updateProfile({
        nickname: form.nickname,
        phone: form.phone,
        email: form.email,
        avatar: form.avatar
    })
    ElMessage.success('个人资料已更新')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '更新失败')
  } finally {
    loading.value = false
  }
}

function handleLogout() {
  authStore.logout()
  ElMessage.success('已退出登录')
}
</script>

<style scoped lang="scss">
.profile-container {
  padding: 40px;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow-y: auto;
}

.glass-card {
  width: 100%;
  max-width: 800px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.05);
  padding: 48px;
}

.header {
  margin-bottom: 40px;
  text-align: center;
  
  h2 {
    font-size: 32px;
    font-weight: 700;
    color: #1f2937;
    margin: 0 0 8px;
  }
  
  p {
    color: #6b7280;
    font-size: 16px;
  }
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  
  .avatar-img {
    border: 4px solid #fff;
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  }
  
  .avatar-edit {
    display: flex;
    justify-content: center;
  }
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.actions {
  margin-top: 32px;
  display: flex;
  justify-content: flex-end;
  
  .save-btn {
    padding: 12px 32px;
    border-radius: 12px;
    font-weight: 600;
  }
}
</style>
