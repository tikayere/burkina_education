import frappeUIPreset from "frappe-ui/tailwind";

/** @type {import('tailwindcss').Config} */
export default {
	presets: [frappeUIPreset],
	content: [
		"./index.html",
		"./src/**/*.{vue,js,ts,jsx,tsx}",
		"./node_modules/frappe-ui/src/components/**/*.{vue,js,jsx,ts,tsx}",
	],
	theme: {
		extend: {
			colors: {
				// École Pilote Burkina brand accents (flag colours) - kept as
				// named tokens (bf-red/bf-green/bf-gold) rather than sprinkling
				// raw hex through the templates, matching hooks.py's app_color.
				"bf-red": {
					50: "#fdf2f2",
					100: "#fce4e4",
					500: "#EF2B2D",
					600: "#d81f21",
					700: "#b01a1c",
				},
				"bf-green": {
					50: "#f0faf4",
					500: "#009E49",
					600: "#00863d",
				},
				"bf-gold": {
					50: "#fffbeb",
					400: "#FCD116",
					500: "#eab308",
				},
			},
			fontFamily: {
				sans: [
					"Inter",
					"ui-sans-serif",
					"system-ui",
					"-apple-system",
					"Segoe UI",
					"Roboto",
					"Helvetica Neue",
					"Arial",
					"sans-serif",
				],
			},
		},
	},
};
