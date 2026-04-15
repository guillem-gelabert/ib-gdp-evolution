<template>
  <svg ref="svg"></svg>
</template>

<script setup lang="ts">
import * as d3 from "d3";
const svg = ref(null);

interface GdpDataPoint {
  year: number;
  gdp_pc: number;
  source: string;
}

const props = defineProps<{
  data: Array<GdpDataPoint>;
}>();

const drawChart = () => {
  const width = 928;
  const height = 500;
  const marginTop = 20;
  const marginRight = 30;
  const marginBottom = 30;
  const marginLeft = 40;

  const svgEl = d3.select(svg.value);
  svgEl.selectAll("*").remove(); // Clear previous renders
  svgEl
    .attr("preserveAspectRatio", "xMinYMin meet")
    .attr("viewBox", "0 0 960 500");

  const domainX = d3
    .extent(props.data, (d) => d.year)
    .map((y) => {
      if (y) {
        return new Date(y, 0, 0);
      }
    })
    .filter((d) => !!d);

  const domainY = d3.extent(props.data, (d) => d.gdp_pc);

  if (
    !domainX[0] ||
    !domainX[1] ||
    !domainY[0] ||
    !domainY[1] ||
    domainX[0] === domainX[1] ||
    domainY[0] === domainY[1]
  ) {
    return;
  }

  const x = d3.scaleTime(domainX, [marginLeft, width - marginRight]);
  const y = d3.scaleLinear(domainY, [height - marginBottom, marginTop]);

  svgEl
    .append("g")
    .attr("transform", `translate(0,${height - marginBottom})`)
    .call(d3.axisBottom(x).tickSizeOuter(0));

  svgEl
    .append("g")
    .attr("transform", `translate(${marginLeft},0)`)
    .call(d3.axisLeft(y).ticks(height / 40))
    .call((g) => g.select(".domain").remove())
    .call((g) =>
      g
        .selectAll(".tick line")
        .clone()
        .attr("x2", width - marginLeft - marginRight)
        .attr("stroke-opacity", 0.1),
    )
    .call((g) =>
      g
        .append("text")
        .attr("x", -marginLeft)
        .attr("y", 10)
        .attr("fill", "currentColor")
        .attr("text-anchor", "start")
        .text("GDP per capita"),
    );

  // Declare the line generator.
  const line = d3.line(
    (d: GdpDataPoint) => {
      return x(new Date(d.year, 0, 0));
    },
    (d: GdpDataPoint) => {
      return y(d.gdp_pc);
    },
  );

  svgEl
    .append("path")
    .attr("fill", "none")
    .attr("stroke", "steelblue")
    .attr("stroke-width", 1.5)
    .attr("d", line(props.data));
};

onMounted(drawChart);

watch(() => props.data, drawChart);
</script>

<style scoped></style>
