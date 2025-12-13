<script>
	import '@evidence-dev/tailwind/fonts.css';
	import '../app.css';
	import { EvidenceDefaultLayout } from '@evidence-dev/core-components';
	export let data;
</script>

<svelte:head>
	<link rel="icon" href="/favicon.svg" type="image/svg+xml" />
	<link rel="apple-touch-icon" href="/favicon.svg" />
</svelte:head>

<EvidenceDefaultLayout {data} neverShowQueries={true}>
	<slot slot="content" />
</EvidenceDefaultLayout>