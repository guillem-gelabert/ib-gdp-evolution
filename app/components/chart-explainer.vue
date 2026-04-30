<template>
  <section
    class="relative"
    :class="layout === 'split' ? 'explainer-split' : ''"
  >
    <figure
      class="sticky top-0 m-0 z-0 explainer-figure"
      :class="
        layout === 'split'
          ? 'p-4 md:p-6'
          : 'w-full h-screen flex flex-col justify-center items-center p-6 md:py-10 md:px-12'
      "
    >
      <div
        class="w-full flex flex-col justify-center"
        :class="layout === 'split' ? 'h-full' : 'max-w-[1200px]'"
      >
        <slot name="chart" :active-step="activeStep" />
      </div>
    </figure>

    <article
      ref="article"
      class="relative z-10"
      :class="layout === 'split' ? 'explainer-text px-6 md:px-12' : 'pointer-events-none'"
    >
      <div
        v-if="layout !== 'split'"
        class="h-[50vh]"
        aria-hidden="true"
      ></div>

      <div
        v-for="(stepContent, index) in steps"
        :key="index"
        class="step"
        :class="
          layout === 'split'
            ? 'flex items-start py-8 md:py-12'
            : 'min-h-screen pl-6 md:pl-0 pointer-events-none flex justify-center items-center'
        "
        :data-step="index + 1"
      >
        <template v-if="layout === 'split'">
          <div class="max-w-[460px]">
            <div
              class="border-l-2 pl-5 transition-colors"
              :class="index === activeStep ? 'border-accent' : 'border-accent/30'"
            >
              <p
                class="font-body text-sm md:text-[0.95rem] leading-[1.65] md:leading-[1.7] m-0 whitespace-pre-line transition-colors"
                :class="index === activeStep ? 'text-ink' : 'text-muted'"
              >
                {{ stepContent.body }}
              </p>
            </div>
          </div>
        </template>
        <template v-else>
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
        </template>
      </div>

      <div
        v-if="layout !== 'split'"
        class="h-screen"
        aria-hidden="true"
      ></div>
    </article>
  </section>
</template>

<script setup lang="ts">
import scrollama from "scrollama";

export interface ExplainerStep {
  body: string;
}

const props = defineProps<{
  steps: Array<ExplainerStep>;
  layout?: "overlay" | "split";
}>();

const activeStep = defineModel<number>("activeStep", { default: 0 });
const article = ref<HTMLElement>();

onMounted(() => {
  const scroller = scrollama();
  const stepEls = Array.from(
    article.value?.querySelectorAll(".step") || [],
  ) as HTMLElement[];

  if (stepEls.length === 0) return;

  if (props.layout === "split") {
    const handleResize = () => {
      const stepH = Math.floor(window.innerHeight * 0.45);
      stepEls.forEach((el) => (el.style.minHeight = stepH + "px"));
      scroller.resize();
    };
    handleResize();
    window.addEventListener("resize", handleResize);
  }

  scroller
    .setup({
      step: stepEls,
      offset: 0.5,
      debug: false,
    })
    .onStepEnter((r) => {
      activeStep.value = r.index;
    });

  window.addEventListener("resize", () => scroller.resize());
});
</script>

<style scoped>
.explainer-split {
  display: flex;
  flex-direction: row;
}
.explainer-split .explainer-figure {
  width: 50%;
  min-width: 0;
  height: 100vh;
}
.explainer-split .explainer-text {
  width: 50%;
  min-width: 0;
}

@media (orientation: portrait) {
  .explainer-split {
    display: grid;
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }
  .explainer-split .explainer-figure,
  .explainer-split .explainer-text {
    grid-column: 1;
    grid-row: 1;
    width: 100%;
  }
  .explainer-split .explainer-figure {
    z-index: 0;
    height: 50vh;
  }
  .explainer-split .explainer-text {
    z-index: 10;
    padding-top: 50vh;
    pointer-events: none;
  }
  .explainer-split .explainer-text :deep(*) {
    pointer-events: auto;
  }
}
</style>
