<script lang="ts">
  import { Badge } from "$lib/components/ui/badge";
  export let appVersion: string | null = null;
</script>

<Badge>v{appVersion ? appVersion : "unknown"}</Badge>
