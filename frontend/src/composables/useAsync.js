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
	// frappe-ui's `toast` is an object (toast.create/success/error/...), not
	// a callable - calling it directly (`toast({...})`) throws instead of
	// showing anything, which is why every success/error notification in
	// every portal has been silently failing (see App.vue's matching fix -
	// this needs both: the right call AND a mounted `<Toasts />` container).
	toast.success(text);
}

export function notifyError(error, fallback = "Une erreur est survenue.") {
	toast.error(error?.messages?.[0] || error?.message || fallback);
}
