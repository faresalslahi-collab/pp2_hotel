import frappeUIPreset from 'frappe-ui/tailwind'

// App-level design tokens -- a distinct `app.*` color namespace and
// `app-*` radius scale, deliberately NOT overriding frappe-ui's own
// `gray`/`blue`/etc. palette or its `sm`/`md`/`lg` radius keys. frappe-ui's
// own components (Button, FormControl, Dialog, ...) are tuned to its own
// scale; redefining those globally would silently change how every
// imported frappe-ui component looks. Custom app components (AppSidebar,
// RoomCard, StatusBadge, ...) use these `app.*`/`app-*` tokens instead, so
// the two systems coexist without collision.
//
// Palette is deliberately hospitality-toned (deep teal/green primary,
// warm neutrals) rather than gcc_hr's blue-based admin-panel palette --
// this is a guest-facing hotel PMS, it should feel calm/premium, not like
// a generic back-office tool.
export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,jsx,ts,tsx}',
    './node_modules/frappe-ui/src/components/**/*.{vue,js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        app: {
          bg: '#F7F8F7',
          surface: '#FFFFFF',
          border: '#E3E7E4',
          text: '#16211D',
          muted: '#5F6B66',
          disabled: '#9CA6A2',
          primary: '#0F5C52',
          'primary-hover': '#0B463F',
          'primary-surface': '#E6F1EF',
          success: '#1E8E5A',
          'success-surface': '#E7F5EC',
          warning: '#B7791F',
          'warning-surface': '#FBF1DF',
          danger: '#C0392B',
          'danger-surface': '#FBEAE8',
          info: '#2563A8',
          'info-surface': '#E9F1FA',
          // Room-status palette -- the single most-reused color mapping in
          // this app (dashboard KPI cards, room grid, room drawer, and
          // later housekeeping board). Define once here, reference by name
          // everywhere, never hardcode a hex for a status elsewhere.
          'room-available': '#1E8E5A',
          'room-available-surface': '#E7F5EC',
          'room-occupied': '#2563A8',
          'room-occupied-surface': '#E9F1FA',
          'room-dirty': '#B7791F',
          'room-dirty-surface': '#FBF1DF',
          // Cleaning sits between Dirty (amber) and Clean (deep teal) in the
          // room lifecycle -- a distinct cyan/sky tone reads as "actively
          // being worked on right now", clearly apart from room-occupied's
          // blue and room-dirty's amber.
          'room-cleaning': '#0E7C93',
          'room-cleaning-surface': '#E3F3F6',
          'room-clean': '#0F5C52',
          'room-clean-surface': '#E6F1EF',
          'room-inspected': '#6B4C9A',
          'room-inspected-surface': '#EFE9F6',
          'room-reserved': '#4C5FD5',
          'room-reserved-surface': '#EBEDFB',
          'room-ooo': '#C0392B',
          'room-ooo-surface': '#FBEAE8',
          'room-maintenance': '#C2660A',
          'room-maintenance-surface': '#FBEEE1',
        },
      },
      borderRadius: {
        'app-sm': '6px',
        'app-md': '8px',
      },
    },
  },
}
