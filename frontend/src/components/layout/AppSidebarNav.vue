<script setup lang="ts">
// Shared nav-tree renderer used by both the desktop rail/expanded aside and
// the mobile off-canvas drawer in AppSidebar.vue -- not in the original
// component list, but the nested tree (unlike gcc_hr's/qcore's flat
// sidebars) needs the same expand/collapse + active-state logic in two
// different shells, and duplicating ~60 lines of template twice in
// AppSidebar.vue itself was worse than one small extra file.
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ChevronDown } from 'lucide-vue-next'
import { NAV_TREE, type NavItem, type NavChild } from '@/router/nav'
import { useUiStore } from '@/stores/ui'
import { useSessionStore } from '@/stores/session'

const props = withDefaults(defineProps<{ collapsed?: boolean }>(), { collapsed: false })
const emit = defineEmits<{ navigate: [] }>()

const route = useRoute()
const ui = useUiStore()
const session = useSessionStore()

// Role-based filtering, first pass: granular per-DocType permissions
// aren't built on the backend yet, so this only checks a coarse role list
// (see router/nav.ts's ADMIN_ROLES doc comment). Filtering happens here,
// not via CSS, so an unauthorized route is never present in the rendered
// tree/DOM at all -- not just visually hidden.
function isVisible(roles?: string[]): boolean {
	return !roles || roles.length === 0 || session.hasAnyRole(roles)
}

const visibleTree = computed<NavItem[]>(() =>
	NAV_TREE.filter((item) => isVisible(item.roles)).map((item) => ({
		...item,
		children: item.children?.filter((child) => isVisible(child.roles)),
	})),
)

function isChildActive(child: NavChild): boolean {
	return route.path === child.route
}

function hasActiveChild(item: NavItem): boolean {
	return (item.children ?? []).some(isChildActive)
}

function isTopActive(item: NavItem): boolean {
	return (item.route !== undefined && route.path === item.route) || hasActiveChild(item)
}

// Route-driven expansion always wins for the branch containing the active
// route, even if the user manually collapsed that section earlier and the
// route then changed back into it -- see stores/ui.ts's doc comment.
function isOpen(item: NavItem): boolean {
	return hasActiveChild(item) || ui.isSectionOpen(item.label)
}

function onParentClick(item: NavItem) {
	if (props.collapsed) {
		// No room for a submenu in the icon-only rail -- expand the sidebar
		// back out and open the section, rather than doing nothing.
		ui.toggleSidebar()
		ui.openSection(item.label)
		return
	}
	ui.toggleSection(item.label)
}

const linkBase = 'flex items-center gap-2.5 rounded-app-sm px-2.5 py-2 text-[13px] leading-[16px] transition-colors'
const linkActive = 'bg-app-primary-surface font-medium text-app-primary'
const linkInactive = 'text-app-text hover:bg-app-bg'

// The collapsed rail's hover label used to be a CSS-only `absolute
// left-full` span inside each link -- simple, but it's real layout
// content that extends well past the rail's own 64px width even while
// invisible (opacity only hides it, it doesn't remove it from flow).
// That inflated `nav`'s own scrollWidth, and per the CSS overflow spec,
// setting *only* `overflow-y: auto` computes `overflow-x` to `auto` too
// (not `visible`) -- so the overflow silently became a horizontal
// scrollbar wedged into the icon rail instead of a tooltip that floats
// over the main content like it's supposed to. Teleporting a single
// `fixed`-position tooltip to `<body>`, positioned from the hovered
// icon's own bounding rect, keeps it entirely outside `nav`'s layout box
// so it can't contribute to that overflow at all.
const hoveredTooltip = ref<{ label: string; top: number; left: number } | null>(null)

function showTooltip(event: MouseEvent, label: string) {
	if (!props.collapsed) return
	const rect = (event.currentTarget as HTMLElement).getBoundingClientRect()
	hoveredTooltip.value = { label, top: rect.top + rect.height / 2, left: rect.right + 8 }
}

function hideTooltip() {
	hoveredTooltip.value = null
}
</script>

<template>
	<nav class="pp2-scroll flex flex-1 flex-col gap-0.5 overflow-y-auto px-2 py-2">
		<template v-for="item in visibleTree" :key="item.label">
			<!-- Top-level leaf link, e.g. Dashboard -->
			<router-link
				v-if="!item.children"
				:to="item.route!"
				:class="[linkBase, isTopActive(item) ? linkActive : linkInactive]"
				@click="emit('navigate')"
				@mouseenter="showTooltip($event, item.label)"
				@mouseleave="hideTooltip"
			>
				<component :is="item.icon" :size="18" class="shrink-0" />
				<span v-if="!collapsed" class="truncate">{{ item.label }}</span>
			</router-link>

			<!-- Section with children -->
			<div v-else class="relative">
				<button
					type="button"
					class="w-full"
					:class="[linkBase, hasActiveChild(item) ? linkActive : linkInactive]"
					@click="onParentClick(item)"
					@mouseenter="showTooltip($event, item.label)"
					@mouseleave="hideTooltip"
				>
					<component :is="item.icon" :size="18" class="shrink-0" />
					<span v-if="!collapsed" class="flex-1 truncate text-left">{{ item.label }}</span>
					<ChevronDown
						v-if="!collapsed"
						:size="15"
						class="shrink-0 text-app-muted transition-transform duration-150"
						:class="isOpen(item) ? 'rotate-180' : ''"
					/>
				</button>

				<div v-if="!collapsed && isOpen(item)" class="ml-4 mt-0.5 space-y-0.5 border-l border-app-border pl-3.5">
					<router-link
						v-for="child in item.children"
						:key="child.route"
						:to="child.route"
						class="block truncate rounded-app-sm px-2.5 py-1.5 text-[13px] leading-[16px] transition-colors"
						:class="isChildActive(child) ? linkActive : linkInactive"
						@click="emit('navigate')"
					>
						{{ child.label }}
					</router-link>
				</div>
			</div>
		</template>
	</nav>

	<Teleport to="body">
		<div
			v-if="hoveredTooltip"
			role="tooltip"
			class="pointer-events-none fixed z-50 -translate-y-1/2 whitespace-nowrap rounded-app-sm bg-app-text px-2 py-1 text-xs text-white shadow-lg"
			:style="{ top: `${hoveredTooltip.top}px`, left: `${hoveredTooltip.left}px` }"
		>
			{{ hoveredTooltip.label }}
		</div>
	</Teleport>
</template>
