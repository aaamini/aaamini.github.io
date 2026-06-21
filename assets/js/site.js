const MATHJAX_SRC = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js";
const TEX_PATTERN = /(?:\$\$?|\\\(|\\\[)/;
let mathJaxPromise;

function ensureMathJax() {
  if (window.MathJax?.typesetPromise) return Promise.resolve(window.MathJax);
  if (mathJaxPromise) return mathJaxPromise;

  mathJaxPromise = new Promise((resolve, reject) => {
    const existing = document.getElementById("MathJax-script");
    if (existing) {
      existing.addEventListener("load", () => resolve(window.MathJax), { once: true });
      existing.addEventListener("error", reject, { once: true });
      return;
    }

    window.MathJax = {
      tex: { inlineMath: [["$", "$"], ["\\(", "\\)"]], processEscapes: true },
      options: { skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code"] },
      startup: { typeset: false }
    };

    const script = document.createElement("script");
    script.id = "MathJax-script";
    script.src = MATHJAX_SRC;
    script.async = true;
    script.addEventListener("load", () => resolve(window.MathJax), { once: true });
    script.addEventListener("error", reject, { once: true });
    document.head.append(script);
  });

  return mathJaxPromise;
}

document.addEventListener("click", (ev) => {
  const btn = ev.target.closest("[data-toggle]");
  if (!btn) return;
  const el = document.getElementById(btn.dataset.toggle);
  if (!el) return;

  const opening = el.hidden;
  el.hidden = !el.hidden;

  if (opening && !el.matches("pre") && TEX_PATTERN.test(el.textContent || "")) {
    ensureMathJax()
      .then((mathJax) => mathJax.typesetPromise?.([el]))
      .catch(() => {});
  }
});
