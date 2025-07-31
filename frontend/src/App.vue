<template>
  <div id="app">
    <el-container style="height: 100vh">
      <!-- Header -->
      <el-header style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; line-height: 60px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
        <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
          <el-icon style="font-size: 28px; margin-right: 12px; color: #ffd700;">
            <TrendCharts />
          </el-icon>
          <h1 style="margin: 0; font-size: 28px; font-weight: 700; letter-spacing: 1px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            NiceAMS
          </h1>
        </div>
      </el-header>
      
      <el-container>
        <!-- Sidebar -->
        <el-aside width="250px" style="background-color: #f8f9fa">
          <el-menu
            :default-active="$route.path"
            mode="vertical"
            router
            style="height: 100%"
          >
            <el-menu-item index="/">
              <el-icon><HomeFilled /></el-icon>
              <span>Dashboard</span>
            </el-menu-item>
            <el-menu-item index="/portfolio">
              <el-icon><TrendCharts /></el-icon>
              <span>Portfolio</span>
            </el-menu-item>
            <el-menu-item index="/transactions">
              <el-icon><List /></el-icon>
              <span>Transactions</span>
            </el-menu-item>
            <el-menu-item index="/assets">
              <el-icon><Goods /></el-icon>
              <span>Assets</span>
            </el-menu-item>
            <el-menu-item index="/analytics">
              <el-icon><DataAnalysis /></el-icon>
              <span>Analytics</span>
            </el-menu-item>
            <el-menu-item index="/settings">
              <el-icon><Setting /></el-icon>
              <span>Settings</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <!-- Main Content -->
        <el-main style="background-color: #ffffff">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { TrendCharts } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    TrendCharts
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

body {
  margin: 0;
  padding: 0;
}

.el-header {
  padding: 0 20px;
}

.el-aside {
  border-right: 1px solid #e6e6e6;
}

.el-main {
  padding: 20px;
}
</style>