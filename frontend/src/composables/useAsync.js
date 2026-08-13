import { ref, watch } from "vue";
import { toast } from "frappe-ui";

/**
 * Small fetch-on-mount(-and-on-`watchSource`-change) helper - every portal
 * page follows the same shape (loading / error / data), so this is the one
 * place that shape is implemented rather than fifteen copies of the same
 * try/catch/finally.
 */
export function useAsync(fetcher, { watchSource = null, initial = null } = {}) {
	const data = ref(initial);
	const loading = ref(true);
	const error = ref(null);

	async function load() {
		loading.value = true;
		error.value = null;
		try {
			data.value = await fetcher();
		} catch (e) {
			error.value = e?.messages?.[0] || e?.message || "Une erreur est survenue.";
		} finally {
			loading.value = false;
		}
	}

	if (watchSource) {
		watch(watchSource, load, { immediate: true });
	} else {
		load();
	}

	return { data, loading, error, reload: load };
}

export function notifySuccess(text) {
	toast({ title: text, icon: "check-circle", iconClasses: "text-bf-green-500" });
}

export function notifyError(error, fallback = "Une erreur est survenue.") {
	toast({
		title: error?.messages?.[0] || error?.message || fallback,
		icon: "alert-circle",
		iconClasses: "text-bf-red-500",
	});
}
