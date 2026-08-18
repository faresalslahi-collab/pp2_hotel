<script setup lang="ts">
// Generic placeholder used by every sidebar destination except Dashboard
// this phase (see router/index.ts -- every route generated from
// router/nav.ts renders this, driven entirely by static route props/meta,
// no per-page file needed for the ~60 not-yet-built destinations).
import PageContainer from '@/components/layout/PageContainer.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

withDefaults(defineProps<{ title: string; description?: string }>(), {
	description: 'Coming in a later phase.',
})
</script>

<template>
	<PageContainer>
		<div class="flex min-h-[60vh] items-center justify-center">
			<EmptyState :title="title" :description="description" />
		</div>
	</PageContainer>
</template>
