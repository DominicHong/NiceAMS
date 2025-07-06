<template>
  <div id="app">
    <el-container style="height: 100vh">
      <!-- Header -->
      <el-header style="background-color: #545c64; color: white; text-align: center; line-height: 60px">
        <h1>Portfolio Tracker</h1>
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
export default {
  name: 'App'
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