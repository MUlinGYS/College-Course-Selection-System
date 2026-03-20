<template>
  <section class="page-stack">
    <article class="panel-card centered-card">
      <p class="eyebrow">404</p>
      <h1>页面不存在</h1>
      <p class="muted">该地址不匹配任何已注册页面，请返回系统主界面。</p>
      <div class="toolbar center-toolbar">
        <RouterLink class="primary-btn link-btn" to="/profile">返回系统</RouterLink>
      </div>
    </article>
  </section>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>
