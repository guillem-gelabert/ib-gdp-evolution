<template>
  <div>
    <h1>Evolució del PIB de les Illes Balears</h1>
    <line-chart :data="parsed" />
  </div>
</template>

<script setup lang="ts">
import { csvParse } from "d3";
const { data } = await useFetch("/data/ib-gdp-absolute.csv", {
  server: false,
});

const parsed = computed(() => {
  if (typeof data.value === "string") {
    console.log(data.value);
    return csvParse(data.value).map((d) => ({
      year: +d.year!,
      gdp_pc: parseFloat(d.value),
      source: d.source!,
    }));
  }
  return [];
});
</script>
