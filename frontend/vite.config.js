import path from "path";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig(async () => {
	const { default: frappeui } = await import("frappe-ui/vite");

	return {
		plugins: [
			frappeui({
				frontendRoute: "/portal",
				jinjaBootData: true,
			}),
			vue(),
		],
		resolve: {
			alias: {
				"@": path.resolve(__dirname, "src"),
			},
		},
	};
});
