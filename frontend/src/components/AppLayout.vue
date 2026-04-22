<script setup lang="ts">
import { ElHeader, ElContainer, ElAside, ElMain } from 'element-plus'
import AppHeader from './AppHeader.vue'
import AppFooter from './AppFooter.vue'
</script>

<template>
  <el-container class="min-h-screen bg-gray-50">
    <el-header class="bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <AppHeader />
    </el-header>
    <el-container>
      <el-main class="p-6">
        <slot />
      </el-main>
    </el-container>
    <AppFooter />
  </el-container>
</template>
