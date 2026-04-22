<script setup lang="ts">
import { ElCard, ElRow, ElCol, ElStatistic } from 'element-plus'
</script>

<template>
  <div>
    <h1 class="text-3xl font-bold text-black mb-6">首页</h1>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="mb-4">
          <el-statistic title="活跃用户" :value="12568" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="mb-4">
          <el-statistic title="总订单" :value="35689" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="mb-4">
          <el-statistic title="总收入" :value="¥125680.00" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="mt-4">
      <template #header>
        <h2 class="text-xl font-semibold">欢迎使用模板项目</h2>
      </template>
      <div class="text-gray-600">
        <p class="mb-4">这是一个基于 Vue 3 + TypeScript + Vite + Pinia + Tailwind CSS 的前后端分离模板项目。</p>
        <p>前端技术栈：Vue 3, TypeScript, Vite, Pinia, Vue Router, Axios, Tailwind CSS, Element Plus</p>
      </div>
    </el-card>
  </div>
</template>
