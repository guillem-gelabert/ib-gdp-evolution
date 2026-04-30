<template>
  <div
    class="font-body min-h-[1280px] bg-cream text-ink text-[17px] leading-[1.65] overflow-clip"
  >
    <svg xmlns="http://www.w3.org/2000/svg" class="hidden">
      <defs>
        <filter
          id="shadow"
          filterUnits="objectBoundingBox"
          x="-40%"
          y="-40%"
          width="180%"
          height="180%"
        >
          <feTurbulence
            type="turbulence"
            baseFrequency="0.6"
            numOctaves="2"
            result="turbulence"
          />
          <feDisplacementMap
            in2="turbulence"
            in="SourceGraphic"
            scale="20"
            xChannelSelector="R"
            yChannelSelector="G"
            result="grainyShadow"
          />
          <feDisplacementMap
            in2="turbulence"
            in="SourceGraphic"
            scale="80"
            xChannelSelector="R"
            yChannelSelector="G"
            result="grainyShadow2"
          />
          <feColorMatrix
            in="grainyShadow"
            result="colorCorrected"
            type="matrix"
            values="1 0 0 -1 0
                  0 0 0 -1 0
                  0 0 0 -1 0
                  0 0 0 1 0"
          />
          <feColorMatrix
            in="grainyShadow2"
            result="colorCorrected2"
            type="matrix"
            values="1 0 0 -1 0
                  0 0 0 -1 0
                  0 0 0 -1 0
                  0 0 0 1 0"
          />

          <feMerge>
            <feMergeNode in="colorCorrected" />
            <feMergeNode in="colorCorrected2" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
    </svg>
    <main>
      <section
        id="hero"
        ref="hero"
        class="relative flex flex-col items-center text-center px-6 md:px-8 bg-cream min-h-screen"
      >
        <div
          class="flex-1 relative z-[6] bg-cream w-full pointer-events-none"
          aria-hidden="true"
        ></div>
        <div
          ref="heroContent"
          class="relative z-10 flex flex-col items-center bg-cream"
        >
          <span
            class="block font-label text-[0.625rem] uppercase tracking-[0.4em] text-accent mb-8"
          >
            Special Investigation
          </span>
          <h1
            class="font-headline text-[clamp(2.5rem,6vw,4.5rem)] font-normal leading-[0.95] tracking-[-0.02em] text-ink mb-8 max-w-4xl text-center"
          >
            Everyone in Mallorca Agrees on One Thing
          </h1>
          <p
            class="font-headline italic text-[1.35rem] text-muted max-w-2xl leading-normal text-center"
          >
            That tourism made the islands rich. The data tells a more
            complicated story.
          </p>
          <div class="w-16 h-[0.5px] bg-rule mx-auto mt-12 mb-6"></div>
          <span
            class="block font-label text-[0.625rem] uppercase tracking-[0.4em] text-muted mb-2"
          >
            Scroll to begin
          </span>
        </div>
        <div
          class="flex-1 relative z-[-1] w-full pointer-events-none"
          aria-hidden="true"
        ></div>
        <div
          ref="scrollArrowContainer"
          class="absolute left-1/2 -translate-x-1/2 top-[-33.333vh] [clip-path:inset(0)] h-[133.333vh] w-[10px] flex justify-center items-start"
        >
          <svg
            ref="scrollArrow"
            class="sticky z-0 text-muted"
            :style="{
              top: `${scrollArrowStickyTop}px`,
            }"
            width="10"
            :height="scrollArrowHeight"
            :viewBox="`0 0 10 ${scrollArrowHeight}`"
            fill="none"
            stroke="currentColor"
            stroke-width="1"
            aria-hidden="true"
          >
            <defs>
              <marker
                id="scroll-arrow-head"
                viewBox="0 0 10 10"
                refX="0"
                refY="5"
                markerWidth="5"
                markerHeight="5"
                orient="auto-start-reverse"
              >
                <path d="M0 0 L0 10 L9 5 Z" fill="currentColor" stroke="none" />
              </marker>
            </defs>
            <path
              :d="`M5 1 L5 ${scrollArrowHeight - 9}`"
              marker-end="url(#scroll-arrow-head)"
              stroke-linecap="butt"
            />
          </svg>
        </div>
      </section>

      <section class="max-w-4xl mx-auto px-6 pb-4 md:px-8 md:pb-6 mt-32">
        <div
          class="max-w-2xl mx-auto text-left font-body text-[1rem] leading-[1.7] text-ink space-y-4"
        >
          <p>
            Tourism accounts for 45.5% of Balearic GDP. It built the roads, the
            hospitals, the airport. It is, by almost every account, the reason
            the islands look the way they do today.
          </p>
          <p>
            Mallorca sells a fantasy of ease: turquoise coves, stone villages,
            long lunches under plane trees, the Mediterranean at its most
            fluent. The island is lively, safe, and — by the numbers — rich. The
            Balearic Islands rank as the 4th wealthiest region in Spain by GDP
            per capita (€36,093 in 2024), and sit right at the EU average.
          </p>
          <p>But this wasn't always the case.</p>
          <p>
            Ask the elderly: it was a poor — if not miserable — agrarian,
            illiterate island. Until tourism came and brought jobs,
            infrastructure, investment, and decades of growth.
          </p>
          <p>
            Hoteliers say it. Their critics concede it, begrudgingly, on the way
            to arguing about what comes next. From the left to the right, from
            the developers to the housing activists, this is the rare point of
            consensus — and the data backs it up.
          </p>
        </div>
      </section>

      <!-- Act 1: Balearic GDP story -->
      <chart-explainer v-model:active-step="act1Step" :steps="act1Steps">
        <template #chart>
          <div class="mb-4">
            <span
              class="font-label text-[0.6875rem] uppercase tracking-[0.15em] font-bold text-accent"
            >PIB per Càpita</span>
          </div>
          <line-chart
            :data="act1Sliced"
            :y-domain="act1YDomain"
            :x-domain="act1XDomain"
            :secondary-data="slicedTourists"
            :secondary-y-domain="touristYDomain"
          />
        </template>
      </chart-explainer>

      <section
        id="outro"
        class="max-w-4xl mx-auto px-6 md:px-8 min-h-screen flex items-center"
      >
        <div
          class="max-w-2xl mx-auto text-left font-body text-[1rem] leading-[1.7] text-ink space-y-4"
        >
          <p>
            That is the story. It is the story your grandmother tells. It is the
            story the hotel lobby tells. It is the story the housing activist
            tells, on their way to arguing about what to do with all the money
            tourism supposedly brings. It is a story that almost everyone in the
            Balearics believes.
          </p>
        </div>
      </section>

      <!-- Act 2: Comparative GDP story -->
      <chart-explainer v-model:active-step="act2Step" :steps="act2Steps">
        <template #chart>
          <div class="mb-4 flex items-end justify-between gap-4">
            <div>
              <span
                class="font-label text-[0.6875rem] uppercase tracking-[0.15em] font-bold text-accent"
              >
                Act II · Comparative GDP per Capita
              </span>
              <p class="mt-2 font-body text-sm text-muted">
                {{
                  act2ActiveConfig.axisMode === "pct-eu15"
                    ? "% of EU-15 average"
                    : "Real GDP per capita"
                }}
              </p>
            </div>
          </div>

          <act2-chart
            :series-map="act2SeriesMap"
            :axis-mode="act2ActiveConfig.axisMode"
            :series-state="act2ActiveConfig.state"
            :show-reference-line="act2ActiveConfig.axisMode === 'pct-eu15'"
            :show-peak-band="act2ActiveConfig.showPeakBand"
            :arrivals-data="act2ParsedArrivals"
            :arrivals-y-domain="act2ArrivalsYDomain"
            :show-arrivals="act2ActiveConfig.showArrivals"
          />
        </template>
      </chart-explainer>

      <section
        id="act3"
        class="max-w-4xl mx-auto px-6 md:px-8 mt-32 mb-16"
      >
        <div
          class="max-w-2xl mx-auto text-left font-body text-[1rem] leading-[1.7] text-ink space-y-5"
        >
          <h2
            class="font-headline text-[clamp(1.5rem,3vw,2.25rem)] font-normal leading-[1.05] tracking-[-0.02em] text-ink mb-8"
          >
            Why?
          </h2>
          <p>
            The honest answer is that no one knows for certain. But there are
            hypotheses, and they are not mutually exclusive.
          </p>
          <ul class="list-none space-y-4 pl-0">
            <li>
              <strong class="text-accent">Productivity ceiling.</strong> Tourism
              is a service industry. Service productivity grows slower than
              manufacturing — a waiter in 2024 cannot serve dramatically more
              tables than a waiter in 1990. Economists call this Baumol's cost
              disease: when an economy concentrates in low-productivity-growth
              sectors, it falls behind economies that diversify.
            </li>
            <li>
              <strong class="text-accent">Monoculture risk.</strong> When 45% of
              GDP flows through a single sector, capital, talent, and policy all
              orient around it. Alternative industries struggle to compete for
              labor, land, or political attention. The economy does not diversify
              because the dominant sector absorbs every resource that might
              enable diversification.
            </li>
            <li>
              <strong class="text-accent">Low-wage lock-in.</strong> Hospitality
              wages are structurally below the national median. A regional
              economy built on hospitality employment drags its per-capita
              figures downward, even as total output grows.
            </li>
            <li>
              <strong class="text-accent">Spanish productivity stagnation.</strong>
              Spain as a whole experienced a productivity slowdown after 1990.
              The Balearic drift may be partly national, not purely local — but
              the islands drifted further and faster than the national average.
            </li>
            <li>
              <strong class="text-accent">Island constraints.</strong> Small
              market, transport costs, land scarcity, seasonal demand swings.
              These are structural limits that no amount of tourism volume can
              overcome — and that tourism volume may, in some cases, worsen.
            </li>
          </ul>
          <p class="text-muted italic">
            The piece's job is to puncture the myth, not to replace it with a
            new one. These are the directions the evidence points. The debate
            about which matters most is a debate worth having — but it is a
            debate that cannot begin until the myth is on the table.
          </p>
        </div>
      </section>

      <section
        id="act4"
        class="max-w-4xl mx-auto px-6 md:px-8 mt-16 mb-32"
      >
        <div
          class="max-w-2xl mx-auto text-left font-body text-[1rem] leading-[1.7] text-ink space-y-5"
        >
          <div class="w-16 h-[0.5px] bg-rule mx-auto mb-12"></div>
          <p>
            Your grandmother is not wrong. The island she grew up on was poor,
            and the island you live on is not. That part of the story is real.
          </p>
          <p>
            But it isn't only a Balearic story. It's a Spanish story, and a
            European one. The same decades that transformed Mallorca transformed
            Extremadura, and Galicia, and Portugal, and the whole arc of southern
            Europe. What happened here happened almost everywhere the war had
            left behind.
          </p>
          <p>
            Tourism was the shape it took on our islands. It is not the reason
            it happened.
          </p>
        </div>
      </section>

      <section
        id="data-methods"
        class="max-w-4xl mx-auto px-6 pb-20 md:px-8 md:pb-24 mt-24"
      >
        <div class="max-w-2xl mx-auto text-left text-ink">
          <h2
            class="font-headline text-[1.5rem] leading-tight tracking-[-0.01em] mb-5"
          >
            Data &amp; Methods
          </h2>
          <div
            class="font-body text-[0.95rem] md:text-[1rem] leading-[1.7] space-y-4 text-muted"
          >
            <p>
              This visual shows a single GDP-per-capita series for the Balearic
              Islands in constant 2011 PPP dollars. It splices two sources:
              Rosés-Wolf decadal estimates for 1900–1999, and INE annual GDP per
              capita chain-linked to the Rosés-Wolf 2000 level for 2000–2024.
            </p>
            <p>
              Values are loaded from
              <code>/public/data/balearic_gdp_pc.csv</code>.
            </p>
            <p>
              Act II uses proxy comparison CSVs under
              <code>/public/data/act2_*.csv</code>, generated from the
              checked-in comparison series already present in the repo.
            </p>
            <p>
              The scrollytelling sequence reveals progressively wider year
              ranges (from 1900 through 2024) to show timing and direction of
              change. Narrative claims in the text are descriptive and based on
              these plotted series.
            </p>
          </div>
        </div>
      </section>
    </main>

    <footer
      class="bg-footer-bg border-t border-rule-light py-16 px-8 text-center"
    >
      <div
        class="font-headline text-base font-bold tracking-[-0.01em] text-ink mb-6"
      >
        GUILLEM GELABERT SUNYER
      </div>
      <div class="w-24 h-[0.5px] bg-rule-light mx-auto mb-6"></div>
      <div
        class="font-label text-[0.625rem] uppercase tracking-[0.15em] text-accent-dark opacity-60"
      >
        © 2024 GGS
      </div>
    </footer>
  </div>

  <!-- debug overlay -->
  <div
    class="fixed bottom-4 right-4 z-[9999] font-body text-[11px] bg-ink/80 text-cream px-3 py-2 rounded pointer-events-none tabular-nums"
  >
    <div>act1 step {{ act1Step + 1 }} / {{ act1Steps.length }}</div>
    <div>act2 step {{ act2Step + 1 }} / {{ act2Steps.length }}</div>
  </div>
</template>

<script setup lang="ts">
import { csvParse, extent as d3Extent } from "d3";
import type { GdpDataPoint } from "./line-chart.vue";

const hero = ref<HTMLElement | null>(null);
const heroContent = ref<HTMLElement | null>(null);
const scrollArrowContainer = ref<HTMLElement | null>(null);
const scrollArrow = ref<SVGSVGElement | null>(null);
const scrollArrowStickyTop = ref(0);
const scrollArrowHeight = ref(418);

const computeArrowStickyTop = () => {
  if (!scrollArrowContainer.value || !heroContent.value) return;
  scrollArrowHeight.value = Math.round(window.innerHeight);
  const contentBottomPageY =
    heroContent.value.getBoundingClientRect().bottom + window.scrollY;
  const headReveal = 50;
  scrollArrowStickyTop.value =
    contentBottomPageY + headReveal - scrollArrowHeight.value;
};

onMounted(() => {
  computeArrowStickyTop();
  window.addEventListener("resize", computeArrowStickyTop);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", computeArrowStickyTop);
});

// ─── Act 1: Balearic GDP ────────────────────────────────────────────

const act1Step = ref(0);

const act1Steps = [
  {
    body: "At the turn of the twentieth century, the Balearics were a rural economy built on almonds, olives, figs, fishing, and the slow, patient work of getting by.",
    from: 1900,
    to: 1910,
    xMax: 1990,
  },
  {
    body: "Most islanders could not read. Most had never left the island. Many who did leave, left for good — to Cuba, to Argentina, to Algeria — sending money home in envelopes that sometimes arrived and sometimes didn't.",
    from: 1900,
    to: 1920,
    xMax: 1990,
  },
  {
    body: "The line on this chart is the Balearic economy, measured in GDP per person. Notice how little it moves. For the first three decades of the century, the average Mallorcan was neither meaningfully richer nor meaningfully poorer from one year to the next. Life happened. The line didn't.",
    from: 1900,
    to: 1930,
    xMax: 1990,
  },
  {
    body: "Then the Civil War. Then the decades Spain spent cut off from the world, rationing bread and stretching lentils.",
    from: 1900,
    to: 1937,
    xMax: 1990,
  },
  {
    body: "The elderly who tell you Mallorca was miserable are not exaggerating. They are remembering these years — the forties and fifties, when the island was more isolated, more rural, and in some ways poorer than it had been a generation earlier.",
    from: 1900,
    to: 1944,
    xMax: 1990,
  },
  {
    body: "On the chart, the line barely lifts off the floor. This is the Mallorca of the myth: the one tourism is said to have rescued.",
    from: 1900,
    to: 1950,
    xMax: 1990,
  },
  {
    body: "And then something happened.\nThe first charter flights landed. Hotels rose along coastlines that had been empty the summer before. Waiters, bricklayers, taxi drivers, receptionists — entire professions appeared where there had been almond trees. The airport grew, and grew again, and grew again.",
    from: 1900,
    to: 1955,
    xMax: 1990,
  },
  {
    body: "Within a single generation, Mallorca stopped being a place people left and became a place people arrived in by the millions.",
    from: 1900,
    to: 1960,
    xMax: 1990,
  },
  {
    body: "Look at what happens to the line. After sixty years of flatness, it bends. It climbs. It keeps climbing — through the oil crises, through the Transition, through Spain's entry into Europe, through the arrival of the euro. By the turn of the millennium, a Mallorcan earned several times what their grandparents had.",
    from: 1900,
    to: 1965,
    xMax: 1990,
  },
  {
    body: "This is the part of the story everyone remembers. This is the part that feels, looking at the chart, undeniable.",
    from: 1900,
    to: 1990,
    xMax: 1990,
  },
  {
    body: "Today, the average Balearic resident lives in an economy many times larger, per person, than the one their great-grandparents knew. In absolute terms, we are richer than we have ever been.",
    from: 1900,
    to: 2024,
    xMax: 2024,
  },
  {
    body: "It is hard to look at this line and argue with it. Tourism came. The line rose. The islanders stopped being poor.",
    from: 1900,
    to: 2024,
    xMax: 2024,
  },
];

const { data: gdpCsv } = await useFetch("/data/balearic_gdp_pc.csv", {
  server: false,
});

const { data: touristCsv } = await useFetch("/data/tourist_arrivals.csv", {
  server: false,
});

const parsed = computed<Array<GdpDataPoint>>(() => {
  if (typeof gdpCsv.value !== "string") return [];
  return csvParse(gdpCsv.value)
    .map((d) => ({
      year: +d.year!,
      gdp_pc: parseFloat(d.gdp_pc!),
      source: d.source!,
      unit: d.unit!,
    }))
    .filter((d) => !Number.isNaN(d.year) && !Number.isNaN(d.gdp_pc))
    .sort((a, b) => a.year - b.year);
});

const act1Sliced = computed<Array<GdpDataPoint>>(() => {
  const step = act1Steps[act1Step.value];
  if (!step || parsed.value.length === 0) return [];
  return parsed.value.filter(
    (d) => d.year >= step.from && d.year <= step.to,
  );
});

const parsedTourists = computed<Array<GdpDataPoint>>(() => {
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

const TOURIST_FIRST_STEP = 7;
const TOURIST_MAX_YEAR = 1950;
const TOURIST_FULL_STEP = 9;

const slicedTourists = computed<Array<GdpDataPoint>>(() => {
  if (act1Step.value < TOURIST_FIRST_STEP) return [];
  if (parsedTourists.value.length === 0) return [];
  const maxYear = act1Step.value >= TOURIST_FULL_STEP ? 2100 : TOURIST_MAX_YEAR;
  return parsedTourists.value.filter(
    (d) => d.year >= 1900 && d.year <= maxYear,
  );
});

const touristYDomain = computed<[number, number]>(() => {
  if (parsedTourists.value.length === 0) return [0, 1];
  return [0, 20_000_000];
});

const act1YDomain = computed(() => {
  if (parsed.value.length === 0) return [0, 1] as [number, number];
  const ext = d3Extent(parsed.value, (d) => d.gdp_pc);
  return [0, ext[1] ?? 1] as [number, number];
});

const act1XDomain = computed<[number, number]>(() => {
  const step = act1Steps[act1Step.value] ?? act1Steps[0];
  if (!step) return [1900, 1990];
  return [step.from, step.xMax];
});

// ─── Act 2: Comparative GDP ─────────────────────────────────────────

const act2Step = ref(0);

const act2Steps = [
  {
    body: "So: the line climbed. The islanders stopped being poor. And the story we tell ourselves is that tourism is what did it.\n\nThere is one way to check whether that's true. Look at who else got richer in the same years.",
  },
  {
    body: "This is Extremadura. It is the poorest region in Spain. It has no coastline. It has no airport worth the name. In 1960, when the first charter flights were landing in Palma, Extremadura had roughly a million people, most of them working land that had been worked the same way for centuries.\n\nWatch what its line does anyway.",
  },
  {
    body: "Extremadura's economy grew in the same decades as ours. Not as fast. Not as high. But the curve is the same curve: a long flat century, then a bend, then a climb.\n\nExtremadura had no Magaluf. No Playa de Palma. No hotels built on the coast because there is no coast. And still, its line goes up. In the same years. For roughly the same reasons we are about to discuss.",
  },
  {
    body: "It isn't just Extremadura. Andalucia did it. Portugal did it. Ireland did it faster than anyone.\n\nWhat all of these places share is not tourism. What they share is the second half of the twentieth century: the end of autarky, the opening of trade, the arrival of foreign capital, the construction of welfare states, the long European peace, eventually EU membership. The tailwind was continental. Every region caught some of it.\n\nWe caught ours through tourism. Extremadura caught theirs through something else. Ireland caught theirs through yet another thing. The wind was the same wind.",
  },
  {
    body: "Which leaves us with an uncomfortable question. If the climb wasn't tourism — if the climb was a thing that was happening anyway, to regions that had nothing like our industry — then what, exactly, did tourism do for the Balearics?\n\nThere is one way to answer that. Stop asking how much. Start asking compared to whom.",
  },
  {
    body: "Same data. Different question. The GDP lines have just been re-indexed against the European average.\n\nThe arrivals line hasn't moved. It can't be re-indexed — there is no European average of \"tourists per region.\" It is what it has always been: a count, climbing.",
  },
  {
    body: "For three decades, the two lines moved together. Both climbing. Both telling the same story.\n\nAnd then, around 1990, the GDP line stopped climbing. The arrivals line didn't.\n\nThe arrivals line kept doing what it had always done. More flights, more hotels, more visitors. A new record almost every year, announced from a podium in front of a logo, applauded by industry and government and most of the press.\n\nMeanwhile — quietly, on the same chart, on the same x-axis — the relative GDP line started drifting downward. Not crashing. Drifting. Year after year, summer after record-breaking summer, the islands' position on the European scoreboard slipped a little further back.\n\nThis is the picture the myth does not survive.",
  },
  {
    body: "Meanwhile, the neighbors kept moving. Ireland kept climbing. Portugal held more steady. Extremadura continued its slower convergence — slowly, steadily, the way it had been doing the whole time.\n\nThe Balearics are among the few European regions that reached a peak, in relative terms, and then spent the following decades falling away from it.",
  },
  {
    body: "Two lines. One x-axis. From 1960 to 1990, they climb together. From 1990 to today, they don't.\n\nThe climb was not unique to us. The fall is. And every record-breaking summer since 1990 has happened on the way down.",
  },
];

const act2SlugToPath: Record<string, string> = {
  balearic_islands: "/data/act2_balearic_islands.csv",
  extremadura: "/data/act2_extremadura.csv",
  andalucia: "/data/act2_andalucia.csv",
  portugal: "/data/act2_portugal.csv",
  ireland: "/data/act2_ireland.csv",
  france: "/data/act2_france.csv",
  eu15_avg: "/data/act2_eu15_avg.csv",
};

const act2Fetches = await Promise.all(
  Object.entries(act2SlugToPath).map(async ([slug, path]) => {
    const { data } = await useFetch(path, { server: false });
    return [slug, data] as const;
  }),
);

const act2SeriesMap = computed<Record<string, Array<GdpDataPoint>>>(() => {
  return Object.fromEntries(
    act2Fetches.map(([slug, data]) => [
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

const act2ParsedArrivals = computed<Array<GdpDataPoint>>(() => {
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

const act2ArrivalsYDomain = computed<[number, number]>(() => {
  if (act2ParsedArrivals.value.length === 0) return [0, 1];
  return [0, 20_000_000];
});

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

const act2ActiveConfig = computed(() => {
  return act2Configs[act2Step.value] ?? act2Configs[0]!;
});
</script>
