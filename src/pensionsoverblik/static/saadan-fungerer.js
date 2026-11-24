/* "Sådan fungerer løsningen" (039b). Åbnet fra beregningen (?fra=beregning) står beregningen i den anden fane,
   og knappen lukker denne fane. Åbnet på anden vis (fx et delt link) går knappen til beregningen. */
const fraBeregningen = new URLSearchParams(location.search).get("fra") === "beregning";
for (const knap of document.querySelectorAll(".tilbage-til-beregningen")) {
  knap.addEventListener("click", () => {
    if (fraBeregningen) window.close();
    // Kunne fanen ikke lukkes (eller blev siden åbnet direkte), går vi til beregningen.
    setTimeout(() => { location.href = "./"; }, fraBeregningen ? 300 : 0);
  });
}
