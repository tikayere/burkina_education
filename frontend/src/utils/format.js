export function formatCurrency(value, currency = "XOF") {
	const amount = Number(value || 0);
	try {
		return new Intl.NumberFormat("fr-FR", {
			style: "currency",
			currency,
			maximumFractionDigits: 0,
		}).format(amount);
	} catch (e) {
		return `${amount.toLocaleString("fr-FR")} ${currency}`;
	}
}

export function formatDate(value, options = { day: "2-digit", month: "short", year: "numeric" }) {
	if (!value) return "-";
	try {
		return new Intl.DateTimeFormat("fr-FR", options).format(new Date(value));
	} catch (e) {
		return value;
	}
}

export function formatDateTime(value) {
	return formatDate(value, {
		day: "2-digit",
		month: "short",
		year: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	});
}

export function formatTime(value) {
	if (!value) return "";
	// Frappe Time fields serialize as "HH:MM:SS" or seconds-since-midnight.
	const str = String(value);
	return str.includes(":") ? str.slice(0, 5) : str;
}

export function initials(name) {
	if (!name) return "?";
	return name
		.split(" ")
		.filter(Boolean)
		.slice(0, 2)
		.map((p) => p[0])
		.join("")
		.toUpperCase();
}

export function relativeDay(value) {
	if (!value) return "-";
	const today = new Date();
	today.setHours(0, 0, 0, 0);
	const date = new Date(value);
	date.setHours(0, 0, 0, 0);
	const diffDays = Math.round((date - today) / 86400000);
	if (diffDays === 0) return "Aujourd'hui";
	if (diffDays === 1) return "Demain";
	if (diffDays === -1) return "Hier";
	return formatDate(value);
}
