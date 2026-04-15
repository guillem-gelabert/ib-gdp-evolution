<template>
  <div>
    <main ref="main">
      <section id="intro">
        <h1 class="intro__hed">Evolució del PIB de les Illes Balears</h1>
        <p class="intro__dek">Start scrolling to see how it works.</p>
      </section>

      <section ref="scrolly" id="scrolly">
        <figure ref="figure">
          <line-chart :data="sliced || []" />
        </figure>

        <article ref="article">
          <div class="step" data-step="1">
            <p>STEP 1</p>
          </div>
          <div class="step" data-step="2">
            <p>STEP 2</p>
          </div>
          <div class="step" data-step="3">
            <p>STEP 3</p>
          </div>
          <div class="step" data-step="4">
            <p>STEP 4</p>
          </div>
          <div class="step" data-step="5">
            <p>STEP 5</p>
          </div>
          <div class="step" data-step="6">
            <p>STEP 6</p>
          </div>
          <div class="step" data-step="7">
            <p>STEP 7</p>
          </div>
          <div class="step" data-step="8">
            <p>STEP 8</p>
          </div>
        </article>
      </section>

      <section id="outro"></section>
    </main>
  </div>
</template>

<script setup lang="ts">
import scrollama from "scrollama";
import { csvParse } from "d3";
import type { GdpDataPoint } from "./components/line-chart.vue";

const figure = ref<HTMLElement>();
const article = ref<HTMLElement>();
const step = ref<Array<HTMLElement>>();

const { data } = await useFetch("/data/ib-gdp-absolute.csv", {
  server: false,
});

const parsed = computed(() => {
  if (typeof data.value === "string") {
    return csvParse(data.value).map((d) => ({
      year: +d.year!,
      gdp_pc: parseFloat(d.value!),
      source: d.source!,
    }));
  }
  return [];
});

const sliced = ref<Array<GdpDataPoint>>([]);

const domains = computed(() => [
  { from: 1900, to: 1950 },
  { from: 1900, to: 1960 },
  { from: 1900, to: 1970 },
  { from: 1900, to: 1980 },
  { from: 1900, to: 1990 },
  { from: 1900, to: 2000 },
  { from: 1900, to: 2010 },
  { from: 1900, to: 2020 },
]);

onMounted(() => {
  const scroller = scrollama();

  step.value = Array.from(article.value?.querySelectorAll(".step") || []);

  function handleResize() {
    // 1. update height of step elements
    var stepH = Math.floor(window.innerHeight * 0.75);
    step.value?.forEach((el: HTMLElement) => (el.style.height = stepH + "px"));

    var figureHeight = window.innerHeight / 2;
    var figureMarginTop = (window.innerHeight - figureHeight) / 2;

    if (figure.value) {
      figure.value.style.height = figureHeight + "px";
      figure.value.style.top = figureMarginTop + "px";
    }

    // 3. tell scrollama to update new element dimensions
    scroller.resize();
  }

  function init() {
    handleResize();
    scroller
      .setup({
        step: ".step",
      })
      .onStepEnter(function handleStepEnter(response) {
        // response = { element, direction, index }

        // add color to current step only
        step.value?.forEach((el: HTMLElement, i: number) => {
          if (i === response.index)
            if (el?.classList?.contains("is-active")) {
              el?.classList?.add("is-active");
            }
        });

        if (parsed.value.length > 0) {
          sliced.value = parsed.value.filter((d: GdpDataPoint) => {
            const key = response.index;
            if (key in domains.value) {
              const domain = domains.value[key];
              if (
                typeof domain === "object" &&
                "from" in domain &&
                "to" in domain
              ) {
                return d.year >= domain.from && d.year <= domain.to;
              }
            }
            return false;
          });
        }
      });
  }

  init();
});
</script>

<style>
* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
}

body {
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu,
    Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
  min-height: 1280px;
  color: #3b3b3b;
  font-size: 24px;
}

p,
h1,
h2,
h3,
h4,
a {
  margin: 0;
  font-weight: 400;
}

a,
a:visited,
a:hover {
  color: teal;
  text-decoration: none;
  border-bottom: 2px solid currentColor;
}

nav {
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  -webkit-box-align: baseline;
  -ms-flex-align: baseline;
  align-items: baseline;
  -webkit-box-pack: justify;
  -ms-flex-pack: justify;
  justify-content: space-between;
  background: #f3f3f3;
  padding: 1rem;
  padding-right: 5rem;
  -ms-flex-wrap: wrap;
  flex-wrap: wrap;
}

.nav__examples {
  display: -webkit-box;
  display: -ms-flexbox;
  display: flex;
  -webkit-box-align: baseline;
  -ms-flex-align: baseline;
  align-items: baseline;
  -ms-flex-wrap: wrap;
  flex-wrap: wrap;
  margin-top: 1rem;
}

.nav__examples > * {
  margin-right: 0.5rem;
}

#intro {
  max-width: 40rem;
  margin: 1rem auto;
  text-align: center;
}

.intro__hed {
  font-size: 2em;
  margin: 2rem auto 0.5rem auto;
}

.intro__dek {
  color: #8a8a8a;
}

.github-corner:hover .octo-arm {
  animation: octocat-wave 560ms ease-in-out;
}

@keyframes octocat-wave {
  0%,
  100% {
    transform: rotate(0);
  }

  20%,
  60% {
    transform: rotate(-25deg);
  }

  40%,
  80% {
    transform: rotate(10deg);
  }
}

@media (max-width: 500px) {
  .github-corner:hover .octo-arm {
    animation: none;
  }

  .github-corner .octo-arm {
    animation: octocat-wave 560ms ease-in-out;
  }
}

#intro {
  margin-bottom: 320px;
}

#outro {
  height: 640px;
}

@media (min-width: 840px) {
  .nav__examples {
    margin-top: 0;
    margin-left: 2rem;
  }
}

#scrolly {
  position: relative;
  background-color: #f3f3f3;
  padding: 1rem;
}

article {
  position: relative;
  padding: 0;
  max-width: 20rem;
  margin: 0 auto;
}

figure {
  position: -webkit-sticky;
  position: sticky;
  left: 0;
  width: 100%;
  margin: 0;
  -webkit-transform: translate3d(0, 0, 0);
  -moz-transform: translate3d(0, 0, 0);
  transform: translate3d(0, 0, 0);
  z-index: 0;
}

figure p {
  text-align: center;
  padding: 1rem;
  position: absolute;
  top: 50%;
  left: 50%;
  -moz-transform: translate(-50%, -50%);
  -webkit-transform: translate(-50%, -50%);
  transform: translate(-50%, -50%);
  font-size: 8rem;
  font-weight: 900;
  color: #fff;
}

.step {
  margin: 0 auto 2rem auto;
  color: #fff;
  background-color: rgba(0, 0, 0, 0.1);
}

.step:last-child {
  margin-bottom: 0;
}

.step.is-active p {
  background-color: goldenrod;
  color: #3b3b3b;
}

.step p {
  text-align: center;
  padding: 1rem;
  font-size: 1.5rem;
  background-color: #3b3b3b;
}
</style>
