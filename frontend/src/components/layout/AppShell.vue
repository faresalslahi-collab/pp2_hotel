<script setup lang="ts">
import AppSidebar from './AppSidebar.vue'
import TopBar from './TopBar.vue'
import Breadcrumbs from './Breadcrumbs.vue'
</script>

<template>
	<div class="flex h-screen overflow-hidden bg-app-bg">
		<AppSidebar />
		<div class="flex min-w-0 flex-1 flex-col">
			<TopBar />
			<Breadcrumbs />
			<main class="pp2-scroll flex-1 overflow-y-auto">
				<router-view />
			</main>
		</div>
	</div>
</template>
