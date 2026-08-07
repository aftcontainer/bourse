(function () {
  "use strict";
  document.addEventListener("DOMContentLoaded", function () {
    const etabSelect    = document.getElementById("id_etablissement");
    const etabBenSelect    = document.getElementById("id_etablissement_ben");
    const titreSelect   = document.getElementById("id_titre");
    const clientSelect  = document.getElementById("id_client");
    const nbportef      = document.getElementById("id_nbportef");
    const nbInput       = document.getElementById("id_nb_titre");
    const nbencoursInput= document.getElementById("id_nbencours");

    const benefSelect    = document.getElementById("id_beneficiaire");
    const nbportefbenInput = document.getElementById("id_nbportefben");
    const totNbportefbenInput = document.getElementById("id_tot_nbportebef");

    const coursInput  = document.getElementById("id_cours_operation");
    const brutInput   = document.getElementById("id_brut");
    const commInput   = document.getElementById("id_commission");
    const tvaInput    = document.getElementById("id_tax");
    const ircmInput   = document.getElementById("id_ircm");
    const cssInput    = document.getElementById("id_css");
    const montantInput= document.getElementById("id_montant");

    if (!etabSelect || !titreSelect || !clientSelect) return;

    // Taux (depuis TYPE_OPERATION via le template, sinon repli)
    let RATES = window.RATES || { commission: 0.01, tva: 0.18, ircm: 0.20, css: 0.01 };
    if (typeof RATES === "string") {
       RATES = JSON.parse(RATES);
    }

    // ---------- Vendeur (clients du portefeuille) ----------
    function setOptions(items, selectedId) {
      let html = '<option value="">---------</option>';
      (items || []).forEach(function (c) {
        const sel = String(c.id) === String(selectedId) ? " selected" : "";
        html += '<option value="' + c.id + '" data-nb="' + (c.nb_titre ?? '') + '"' + sel + '>' + c.text + '</option>';
      });
      clientSelect.innerHTML = html;
      if (window.jQuery && jQuery(clientSelect).data("select2")) jQuery(clientSelect).trigger("change");
    }

    function majNbPortef() {
      // En mode verrouillé, nbportef est déjà fourni par le serveur : on
      // ignore tout "change" (y compris ceux synthétiques de Select2) pour
      // ne jamais l'écraser avec une valeur vide.
      if (window.VERROUILLE) return;
      if (!nbportef) return;
      const val = clientSelect.value;
      const opt = val ? clientSelect.querySelector('option[value="' + val + '"]') : null;
      nbportef.value = (opt && opt.getAttribute("data-nb")) || "";
      calcNbencours();
    }

    function chargerVendeurs() {
      // Rien à faire si le vendeur est verrouillé depuis la page détail du
      // portefeuille : quel que soit le déclencheur (appel initial, "change"
      // synthétique de Select2 lors de son init, etc.), on ne doit jamais
      // vider/recharger le champ pré-rempli et verrouillé côté serveur.
      if (window.VERROUILLE) return;

      const etabId  = etabSelect.value;
      const titreId = titreSelect.value;

      // reset systematique -> les infos du client precedent disparaissent
      clientSelect.innerHTML = '<option value="">---------</option>';
      if (window.jQuery && jQuery(clientSelect).data("select2")) jQuery(clientSelect).trigger("change");
      if (nbportef) nbportef.value = "";

      if (!etabId || !titreId || !window.CLIENTS_URL) {
        clientSelect.innerHTML = '<option value="">(choisir établissement et titre)</option>';
        return;
      }

      clientSelect.disabled = true;
      const url = window.CLIENTS_URL
                + "?titre=" + encodeURIComponent(titreId)
                + "&etablissement=" + encodeURIComponent(etabId);

      fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then((r) => r.json())
        .then((data) => {
          clientSelect.disabled = false;
          const items = data.results || [];
          if (items.length) {
            setOptions(items, null);
          } else {
            clientSelect.innerHTML = '<option value="">Aucun vendeur pour ce titre</option>';
            if (window.jQuery && jQuery(clientSelect).data("select2")) jQuery(clientSelect).trigger("change");
          }
          majNbPortef();
        })
        .catch(() => {
          clientSelect.disabled = false;
          clientSelect.innerHTML = '<option value="">Erreur de chargement</option>';
        });
    }

    // ---------- Nombre total de titres = portefeuille - transaction ----------
    function calcNbencours() {
      if (!nbportef || !nbInput || !nbencoursInput) return;

      const portef = parseInt(nbportef.value, 10);
      const nb     = parseInt(nbInput.value, 10);

      if (isNaN(portef) || isNaN(nb)) {
        nbencoursInput.value = "";
        return;
      }

      const reste = portef - nb;

      if (reste < 0) {
        nbInput.setCustomValidity("Les titres en transaction dépassent le portefeuille (" + portef + ").");
        nbInput.reportValidity();
        nbencoursInput.value = "";
      } else {
        nbInput.setCustomValidity("");
        nbencoursInput.value = reste;
      }
    }

    function calcTotNbporte(){
        if(!nbInput || !nbportefbenInput || !totNbportefbenInput) return;
        const nb = parseInt(nbInput.value,10);
        const portefben = parseInt(nbportefbenInput.value, 10);

        if (isNaN(portefben) || isNaN(nb)) {
            totNbportefbenInput.value = "";
            return;
        }

        const tot = nb + portefben;
        totNbportefbenInput.value = tot;

    }

    // ---------- Montant brut = cours x titres en transaction ----------
    function calcBrut() {
      if (!coursInput || !nbInput || !brutInput) return;

      const cours = parseInt(coursInput.value, 10);
      const nb    = parseInt(nbInput.value, 10);

      if (!isNaN(cours) && !isNaN(nb) && cours >= 10000) {
        brutInput.value = 0 * nb; //cours
      } else {
        brutInput.value = "";
      }
      calcMontants();
    }

    function calcMontants() {
   const targets = [commInput, tvaInput, ircmInput, cssInput, montantInput];

   const brut = parseInt(brutInput && brutInput.value, 10);

   // brut invalide -> on vide proprement (jamais de NaN dans un input number)
   if (!Number.isFinite(brut) || brut <= 0) {
      targets.forEach((el) => { if (el) el.value = ""; });
      return;
   }

   const commission = Math.round(brut * RATES.commission);
   const tva        = Math.round(commission * RATES.tva);
   const ircm       = Math.round(commission * RATES.ircm);
   const css        = Math.round(commission * RATES.css * 100) / 100; // 2 decimales, reste un Number
   const net        = Math.round(brut + commission + tva + ircm + css);

   const vals = { comm: commission, tva: tva, ircm: ircm, css: css, net: net };

   // on n'ecrit que des nombres finis
   if (commInput)    commInput.value    = Number.isFinite(vals.comm) ? vals.comm : "";
   if (tvaInput)     tvaInput.value     = Number.isFinite(vals.tva)  ? vals.tva  : "";
   if (ircmInput)    ircmInput.value    = Number.isFinite(vals.ircm) ? vals.ircm : "";
   if (cssInput)     cssInput.value     = Number.isFinite(vals.css)  ? vals.css  : "";
   if (montantInput) montantInput.value = Number.isFinite(vals.net)  ? vals.net  : "";
}

    function bindChange(el, handler) {
      // Select2 emet son "change" via jQuery -> on ecoute les deux cas
      if (window.jQuery && jQuery(el).data("select2")) {
        jQuery(el).on("change", handler);
      } else {
        el.addEventListener("change", handler);
      }
    }

    bindChange(etabSelect, chargerVendeurs);
    bindChange(titreSelect, chargerVendeurs);

    if (window.jQuery) jQuery(clientSelect).on("change", majNbPortef);
    else clientSelect.addEventListener("change", majNbPortef);

    if (nbInput) {
      nbInput.addEventListener("input", function () { calcNbencours(); calcBrut(); });
    }

    if (coursInput) {
      coursInput.addEventListener("input", calcBrut);
    }

    // Si on vient de la page détail du portefeuille, le vendeur est déjà
    // fourni et verrouillé par le serveur : on ne recharge pas la liste,
    // sinon la sélection pré-remplie serait écrasée.
    if (etabSelect.value && titreSelect.value && !window.VERROUILLE) chargerVendeurs();
    calcNbencours();
    calcBrut();

    function chargerBeneficiaires() {
       const etabId  = etabBenSelect ? etabBenSelect.value : "";
       const titreId = titreSelect.value;

       benefSelect.innerHTML = '<option value="">---------</option>';
       if (window.jQuery && jQuery(benefSelect).data("select2")) jQuery(benefSelect).trigger("change");
       if (nbportefbenInput) nbportefbenInput.value = "";

       if (!etabId || !window.BENEF_URL) {
          benefSelect.innerHTML = '<option value="">(choisir donneur d\'ordre)</option>';
          return;
       }

       benefSelect.disabled = true;
       const url = window.BENEF_URL
                 + "?etablissement=" + encodeURIComponent(etabId)
                 + "&titre=" + encodeURIComponent(titreId);

       fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
          .then((r) => r.json())
          .then((data) => {
             benefSelect.disabled = false;
             const items = data.results || [];
             let html = '<option value="">---------</option>';
             items.forEach((c) => {
                // marque ceux qui possedent deja le titre
                const tag = c.possede ? " • détient (" + c.nb_titre + ")" : " • nouveau";
                html += '<option value="' + c.id + '"'
                      + ' data-nb="' + c.nb_titre + '"'
                      + ' data-possede="' + (c.possede ? "1" : "0") + '">'
                      + c.text + tag + '</option>';
             });
             benefSelect.innerHTML = html;
             if (window.jQuery && jQuery(benefSelect).data("select2")) jQuery(benefSelect).trigger("change");
             majNbPortefBen();
          })
          .catch(() => {
             benefSelect.disabled = false;
             benefSelect.innerHTML = '<option value="">Erreur de chargement</option>';
          });
    }

    function majNbPortefBen() {
       if (!nbportefbenInput || !benefSelect) return;
       const val = benefSelect.value;
       const opt = val ? benefSelect.querySelector('option[value="' + val + '"]') : null;
       // pas de portefeuille -> 0 (data-nb vaut deja "0" depuis la vue)
       nbportefbenInput.value = opt ? (opt.getAttribute("data-nb") || "0") : "";
       calcTotNbporte();
    }

    bindChange(etabBenSelect,chargerBeneficiaires);
    if (window.jQuery) jQuery(benefSelect).on("change", majNbPortefBen);
    else benefSelect.addEventListener("change", majNbPortefBen);
  });
})();
