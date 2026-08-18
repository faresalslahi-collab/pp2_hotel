<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChevronRight } from 'lucide-vue-next'

// Derived purely from route.matched[*].meta.title -- every route this
// phase generates (router/index.ts, from router/nav.ts) sets meta.title,
// so this needs no per-page wiring. Routes are currently flat (a leaf
// path directly under AppShell, not nested further), so today this
// usually renders a single crumb; if a later phase nests routes (e.g. a
// detail page under a list), extra crumbs appear here for free.
interface Crumb {
	label: string
	path: string
}

const route = useRoute()

const crumbs = computed<Crumb[]>(() =>
	route.matched
		.filter((r) => typeof r.meta?.title === 'string')
		.map((r) => ({ label: r.meta.title as string, path: r.path })),
)
</script>

<template>
	<nav v-if="crumbs.length" class="flex items-center gap-1.5 px-4 pt-3 text-[13px] leading-[16px] text-app-muted sm:px-6">
		<template v-for="(crumb, index) in crumbs" :key="crumb.path">
			<span :class="index === crumbs.length - 1 ? 'font-medium text-app-text' : ''">{{ crumb.label }}</span>
			<ChevronRight v-if="index < crumbs.length - 1" :size="14" class="shrink-0 text-app-disabled" />
		</template>
	</nav>
</template>
