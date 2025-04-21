<script lang="ts">
	import { Dialog as DialogPrimitive } from "bits-ui";
	import Cross2 from "svelte-radix/Cross2.svelte";
	import * as Dialog from "./index.js";
	import { cn, flyAndScale } from "$lib/utils.js";
  	import * as Button from "$lib/components/ui/button";

	type $$Props = DialogPrimitive.ContentProps;

	let className: $$Props["class"] = undefined;
	export let transition: $$Props["transition"] = flyAndScale;
	export let transitionConfig: $$Props["transitionConfig"] = {
		duration: 200,
	};
	export { className as class };
</script>

<Dialog.Portal>
	<Dialog.Overlay />
	<DialogPrimitive.Content
		{transition}
		{transitionConfig}
		class={cn(
			"bg-background fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border p-6 shadow-lg sm:rounded-lg md:w-full",
			className
		)}
		{...$$restProps}
	>
		<div class="flex justify-end">
		  <DialogPrimitive.Close class="...">X</DialogPrimitive.Close>
		</div>
		<slot />
	</DialogPrimitive.Content>
</Dialog.Portal>
