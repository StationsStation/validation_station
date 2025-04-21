<script lang="ts">
	import type { HTMLAttributes } from "svelte/elements";
	import { cn } from "$lib/utils.js";

	type $$Props = HTMLAttributes<HTMLDivElement>;

	let className: $$Props["class"] = undefined;
	export { className as class };
</script>

<!-- svelte-ignore a11y-no-static-element-interactions -->
<div
   class={cn(
    // Terminal default styling
    "p-4 space-y-4 text-sm font-mono",
    // Color and UI styling
    "bg-black/70 text-green-300 border border-green-600",
    // Optional fallback/general styles from original
    className
  )}
	{...$$restProps}
	on:click
	on:focusin
	on:focusout
	on:mouseenter
	on:mouseleave
>
	<slot />
</div>
