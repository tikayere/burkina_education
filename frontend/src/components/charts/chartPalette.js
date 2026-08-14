// Shared chart color tokens (dataviz skill: color assigned by job, computed
// once here rather than picked ad hoc per chart).
//
// - BRAND: the one hue used for single-series magnitude/trend charts
//   (attendance evolution, monthly collections) - bf-green, so the portal's
//   own flagship chart (see images/burkina_edu.png's "Évolution des
//   présences") reads as *this app's* color, not a generic default.
// - CATEGORICAL: fixed-order hues for multi-category comparisons (fee by
//   category, admissions funnel) where color encodes identity, not
//   magnitude - the dataviz skill's own validated default ordering (its
//   adjacent-pair/CVD gates already pass; re-deriving a brand-specific set
//   for every slot isn't warranted for a handful of small charts). Assigned
//   in this fixed order, never cycled/re-sorted by value.
// - MUTED: gridlines/axis text - recessive, never a data color.

export const BRAND = "#00863d";
export const BRAND_SOFT = "#00863d22";

export const CATEGORICAL = [
	"#2a78d6", // blue
	"#eb6834", // orange
	"#1baf7a", // aqua
	"#eda100", // yellow
	"#e87ba4", // magenta
	"#008300", // green
	"#4a3aa7", // violet
	"#e34948", // red
];

export const MUTED_GRID = "#e5e7eb"; // gray-200
export const MUTED_TEXT = "#9ca3af"; // gray-400

export function categoricalColor(index) {
	return CATEGORICAL[index % CATEGORICAL.length];
}
