<template>
  <section ref="act2Scrolly" id="act2-scrolly" class="relative mt-20">
    <figure
      class="sticky top-0 w-full h-screen m-0 flex flex-col justify-center items-center z-0 p-6 md:py-10 md:px-12"
    >
      <div class="w-full max-w-[1200px]">
        <div class="mb-4 flex items-end justify-between gap-4">
          <div>
            <span
              class="font-label text-[0.6875rem] uppercase tracking-[0.15em] font-bold text-accent"
            >
              Act II · Comparative GDP per Capita
            </span>
            <p class="mt-2 font-body text-sm text-muted">
              {{
                activeConfig.axisMode === "pct-eu15"
                  ? "% of EU-15 average"
                  : "Real GDP per capita"
              }}
            </p>
          </div>
        </div>

        <act2-chart
          :series-map="seriesMap"
          :axis-mode="activeConfig.axisMode"
          :series-state="activeConfig.state"
          :show-reference-line="activeConfig.axisMode === 'pct-eu15'"
          :show-peak-band="activeConfig.showPeakBand"
          :arrivals-data="parsedArrivals"
          :arrivals-y-domain="arrivalsYDomain"
          :show-arrivals="showArrivals"
        />
      </div>
    </figure>

    <article ref="act2Article" class="relative z-10 pointer-events-none">
      <div
        v-for="(stepContent, index) in act2Steps"
        :key="index"
        class="act2-step snap-center min-h-screen pl-6 md:pl-0 pointer-events-none flex justify-center items-center"
        :data-step="index + 8"
      >
        <div
          class="grid justify-center items-center grid-rows-[min-content] max-w-[490px]"
        >
          <div
            class="bg-[rgba(255,241,229,0.92)] border border-rule-light py-5 px-6 md:py-8 md:px-10 [grid-area:1/1] relative z-0"
          >
            <p
              class="font-body text-sm md:text-[0.95rem] leading-[1.65] md:leading-[1.7] text-muted m-0 whitespace-pre-line"
            >
              {{ stepContent.body }}
            </p>
          </div>
        </div>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import scrollama from "scrollama";
import { csvParse } from "d3";
import type { GdpDataPoint } from "./line-chart.vue";

const act2Article = ref<HTMLElement>();
const activeStep = ref(0);

const act2Steps = [
  {
    title: "The Question",
    body: "So: the line climbed. The islanders stopped being poor. And the story we tell ourselves is that tourism is what did it.\n\nThere is one way to check whether that's true. Look at who else got richer in the same years.",
  },
  {
    title: "Extremadura Enters",
    body: "This is Extremadura. It is the poorest region in Spain. It has no coastline. It has no airport worth the name. In 1960, when the first charter flights were landing in Palma, Extremadura had roughly a million people, most of them working land that had been worked the same way for centuries.\n\nWatch what its line does anyway.",
  },
  {
    title: "The Shape Is the Same",
    body: "Extremadura's economy grew in the same decades as ours. Not as fast. Not as high. But the curve is the same curve: a long flat century, then a bend, then a climb.\n\nExtremadura had no Magaluf. No Playa de Palma. No hotels built on the coast because there is no coast. And still, its line goes up. In the same years. For roughly the same reasons we are about to discuss.",
  },
  {
    title: "And Not Just Extremadura",
    body: "It isn't just Extremadura. Andalucia did it. Portugal did it. Ireland did it faster than anyone.\n\nWhat all of these places share is not tourism. What they share is the second half of the twentieth century: the end of autarky, the opening of trade, the arrival of foreign capital, the construction of welfare states, the long European peace, eventually EU membership. The tailwind was continental. Every region caught some of it.\n\nWe caught ours through tourism. Extremadura caught theirs through something else. Ireland caught theirs through yet another thing. The wind was the same wind.",
  },
  {
    title: "The Pivot",
    body: "Which leaves us with an uncomfortable question. If the climb wasn't tourism — if the climb was a thing that was happening anyway, to regions that had nothing like our industry — then what, exactly, did tourism do for the Balearics?\n\nThere is one way to answer that. Stop asking how much. Start asking compared to whom.",
  },
  {
    title: "The Axis Switch",
    body: "Same data. Different question. The GDP lines have just been re-indexed against the European average.\n\nThe arrivals line hasn't moved. It can't be re-indexed — there is no European average of \"tourists per region.\" It is what it has always been: a count, climbing.",
  },
  {
    title: "The Scissors",
    body: "For three decades, the two lines moved together. Both climbing. Both telling the same story.\n\nAnd then, around 1990, the GDP line stopped climbing. The arrivals line didn't.\n\nThe arrivals line kept doing what it had always done. More flights, more hotels, more visitors. A new record almost every year, announced from a podium in front of a logo, applauded by industry and government and most of the press.\n\nMeanwhile — quietly, on the same chart, on the same x-axis — the relative GDP line started drifting downward. Not crashing. Drifting. Year after year, summer after record-breaking summer, the islands' position on the European scoreboard slipped a little further back.\n\nThis is the picture the myth does not survive.",
  },
  {
    title: "Peers Continue",
    body: "Meanwhile, the neighbors kept moving. Ireland kept climbing. Portugal held more steady. Extremadura continued its slower convergence — slowly, steadily, the way it had been doing the whole time.\n\nThe Balearics are among the few European regions that reached a peak, in relative terms, and then spent the following decades falling away from it.",
  },
  {
    title: "The Hinge",
    body: "Two lines. One x-axis. From 1960 to 1990, they climb together. From 1990 to today, they don't.\n\nThe climb was not unique to us. The fall is. And every record-breaking summer since 1990 has happened on the way down.",
  },
];

const slugToPath: Record<string, string> = {
  balearic_islands: "/data/act2_balearic_islands.csv",
  extremadura: "/data/act2_extremadura.csv",
  andalucia: "/data/act2_andalucia.csv",
  portugal: "/data/act2_portugal.csv",
  ireland: "/data/act2_ireland.csv",
  france: "/data/act2_france.csv",
  eu15_avg: "/data/act2_eu15_avg.csv",
};

const { data: touristCsv } = await useFetch("/data/tourist_arrivals.csv", {
  server: false,
});

const fetches = await Promise.all(
  Object.entries(slugToPath).map(async ([slug, path]) => {
    const { data } = await useFetch(path, { server: false });
    return [slug, data] as const;
  }),
);

const seriesMap = computed<Record<string, Array<GdpDataPoint>>>(() => {
  return Object.fromEntries(
    fetches.map(([slug, data]) => [
      slug,
      typeof data.value === "string"
        ? csvParse(data.value)
            .map((row) => ({
              year: Number(row.year),
              gdp_pc: Number(row.gdp_pc),
              source: row.source ?? slug,
              unit: row.unit,
            }))
            .filter(
              (row) => Number.isFinite(row.year) && Number.isFinite(row.gdp_pc),
            )
        : [],
    ]),
  );
});

const parsedArrivals = computed<Array<GdpDataPoint>>(() => {
  if (typeof touristCsv.value !== "string") return [];
  return csvParse(touristCsv.value)
    .filter((d) => d.display !== "false")
    .map((d) => ({
      year: +d.year!,
      gdp_pc: parseFloat(d.arrivals!),
      source: "Tourists",
      unit: d.source!,
    }))
    .filter((d) => !Number.isNaN(d.year) && !Number.isNaN(d.gdp_pc))
    .sort((a, b) => a.year - b.year);
});

const arrivalsYDomain = computed<[number, number]>(() => {
  if (parsedArrivals.value.length === 0) return [0, 1];
  return [0, 20_000_000];
});

const showArrivals = computed(
  () => activeConfig.value?.showArrivals ?? false,
);

const act2Configs = [
  {
    axisMode: "real-eur" as const,
    showPeakBand: false,
    showArrivals: true,
    state: {
      balearic_islands: { visible: true, emphasis: "highlight" as const },
      extremadura: { visible: false },
      andalucia: { visible: false },
      portugal: { visible: false },
      ireland: { visible: false },
      france: { visible: false },
      eu15_avg: { visible: false },
    },
  },
  {
    axisMode: "real-eur" as const,
    showPeakBand: false,
    showArrivals: true,
    state: {
      balearic_islands: { visible: true, emphasis: "normal" as const },
      extremadura: { visible: true, emphasis: "highlight" as const },
      andalucia: { visible: false },
      portugal: { visible: false },
      ireland: { visible: false },
      france: { visible: false },
      eu15_avg: { visible: false },
    },
  },
  {
    axisMode: "real-eur" as const,
    showPeakBand: false,
    showArrivals: true,
    state: {
      balearic_islands: { visible: true, emphasis: "highlight" as const },
      extremadura: { visible: true, emphasis: "normal" as const },
      andalucia: { visible: false },
      portugal: { visible: false },
      ireland: { visible: false },
      france: { visible: false },
      eu15_avg: { visible: false },
    },
  },
  {
    axisMode: "real-eur" as const,
    showPeakBand: false,
    showArrivals: true,
    state: {
      balearic_islands: { visible: true, emphasis: "normal" as const },
      extremadura: { visible: true, emphasis: "normal" as const },
      andalucia: { visible: true, emphasis: "normal" as const },
      portugal: { visible: true, emphasis: "normal" as const },
      ireland: { visible: true, emphasis: "highlight" as const },
      france: { visible: true, emphasis: "normal" as const },
      eu15_avg: { visible: false },
    },
  },
  {
    axisMode: "real-eur" as const,
    showPeakBand: false,
    showArrivals: true,
    state: {
      balearic_islands: { visible: true, emphasis: "highlight" as const },
      extremadura: { visible: true, emphasis: "muted" as const },
      andalucia: { visible: true, emphasis: "muted" as const },
      portugal: { visible: true, emphasis: "muted" as const },
      ireland: { visible: true, emphasis: "muted" as const },
      france: { visible: true, emphasis: "muted" as const },
      eu15_avg: { visible: false },
    },
  },
  {
    axisMode: "pct-eu15" as const,
    showPeakBand: false,
    showArrivals: true,
    state: {
      balearic_islands: { visible: true, emphasis: "highlight" as const },
      extremadura: { visible: true, emphasis: "muted" as const },
      andalucia: { visible: true, emphasis: "muted" as const },
      portugal: { visible: true, emphasis: "muted" as const },
      ireland: { visible: true, emphasis: "muted" as const },
      france: { visible: true, emphasis: "muted" as const },
      eu15_avg: { visible: true, emphasis: "normal" as const },
    },
  },
  {
    axisMode: "pct-eu15" as const,
    showPeakBand: true,
    showArrivals: true,
    state: {
      balearic_islands: { visible: true, emphasis: "highlight" as const },
      extremadura: { visible: true, emphasis: "muted" as const },
      andalucia: { visible: true, emphasis: "muted" as const },
      portugal: { visible: true, emphasis: "muted" as const },
      ireland: { visible: true, emphasis: "muted" as const },
      france: { visible: true, emphasis: "muted" as const },
      eu15_avg: { visible: true, emphasis: "normal" as const },
    },
  },
  {
    axisMode: "pct-eu15" as const,
    showPeakBand: true,
    showArrivals: true,
    state: {
      balearic_islands: { visible: true, emphasis: "highlight" as const },
      extremadura: { visible: true, emphasis: "normal" as const },
      andalucia: { visible: true, emphasis: "muted" as const },
      portugal: { visible: true, emphasis: "normal" as const },
      ireland: { visible: true, emphasis: "highlight" as const },
      france: { visible: true, emphasis: "muted" as const },
      eu15_avg: { visible: true, emphasis: "normal" as const },
    },
  },
  {
    axisMode: "pct-eu15" as const,
    showPeakBand: true,
    showArrivals: true,
    state: {
      balearic_islands: { visible: true, emphasis: "highlight" as const },
      extremadura: { visible: false },
      andalucia: { visible: false },
      portugal: { visible: false },
      ireland: { visible: false },
      france: { visible: false },
      eu15_avg: { visible: true, emphasis: "normal" as const },
    },
  },
];

const activeConfig = computed(
  () => act2Configs[activeStep.value] ?? act2Configs[0],
);

onMounted(() => {
  const scroller = scrollama();
  const steps = Array.from(
    act2Article.value?.querySelectorAll(".act2-step") || [],
  );
  const handleResize = () => {
    scroller.resize();
  };

  handleResize();
  window.addEventListener("resize", handleResize);
  scroller
    .setup({
      step: steps,
      offset: 0.5,
    })
    .onStepEnter((response) => {
      activeStep.value = response.index;
    });

  onBeforeUnmount(() => {
    window.removeEventListener("resize", handleResize);
  });
});
</script>
