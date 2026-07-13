(function () {
	"use strict";

	document.addEventListener("DOMContentLoaded", function () {
		const typeSelect  = document.getElementById("id_type_titre");
		const titreSelect = document.getElementById("id_titre");
		const clientSelect = document.getElementById("id_client");

		if (!typeSelect || !titreSelect || !window.TITRES_URL) return;

		function chargerTitres(typeId, selectedId) {
			// Reset
			titreSelect.innerHTML = '<option value="">Chargement…</option>';
			titreSelect.disabled = true;

			if (!typeId) {
				titreSelect.innerHTML = '<option value="">--------- (choisissez un type)</option>';
				titreSelect.disabled = false;
				return;
			}

			const url = window.TITRES_URL + "?type_titre=" + encodeURIComponent(typeId);

			fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
				.then((r) => r.json())
				.then((data) => {
					let html = '<option value="">---------</option>';
					(data.results || []).forEach((t) => {
						const sel = String(t.id) === String(selectedId) ? " selected" : "";
						html += `<option value="${t.id}"${sel}>${t.text}</option>`;
					});
					titreSelect.innerHTML = html;
					titreSelect.disabled = false;

					// Si Select2 est branché sur ce champ, on le notifie du changement
					if (window.jQuery && jQuery(titreSelect).data("select2")) {
						jQuery(titreSelect).trigger("change");
					}
				})
				.catch(() => {
					titreSelect.innerHTML = '<option value="">Erreur de chargement</option>';
					titreSelect.disabled = false;
				});
		}

		function chargerClients(titreId, selectedId) {
           const nbportef = document.getElementById("id_nbportef");

           clientSelect.innerHTML = '<option value="">Chargement…</option>';
           clientSelect.disabled = true;
           if (nbportef) nbportef.value = "";

           if (!titreId) {
              clientSelect.innerHTML = '<option value="">--------- (choisissez un titre)</option>';
              clientSelect.disabled = false;
              return;
           }

           const url = window.CLIENTS_URL + "?titre=" + encodeURIComponent(titreId);

           fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
              .then((r) => r.json())
              .then((data) => {
                 let html = '<option value="">---------</option>';
                 (data.results || []).forEach((c) => {
                    const sel = String(c.id) === String(selectedId) ? " selected" : "";
                    html += `<option value="${c.id}" data-nb="${c.nb_titre ?? ''}"${sel}>${c.text}</option>`;
                 });
                 clientSelect.innerHTML = html;
                 clientSelect.disabled = false;

                 // Remplit nbportef si un client est deja pre-selectionne (mode edition)
                 majNbPortef();

                 if (window.jQuery && jQuery(clientSelect).data("select2")) {
                    jQuery(clientSelect).trigger("change");
                 }
              })
              .catch(() => {
                 clientSelect.innerHTML = '<option value="">Erreur de chargement</option>';
                 clientSelect.disabled = false;
              });
        }

        // Recopie le data-nb de l'option choisie dans le champ nbportef
//        function majNbPortef() {
//           const nbportef = document.getElementById("id_nbportef");
//           if (!nbportef || !clientSelect) return;
//           const opt = clientSelect.options[clientSelect.selectedIndex];
//           console.log("client:", clientSelect.value, "data-nb:", opt && opt.getAttribute("data-nb"));
//           nbportef.value = (opt && opt.getAttribute("data-nb")) || "";
//        }

        if (window.jQuery) {
           jQuery(clientSelect).on("change", majNbPortef);   // capte le change de Select2
        } else {
           clientSelect.addEventListener("change", majNbPortef);
        }

        function majNbPortef() {
           const nbportef = document.getElementById("id_nbportef");
           if (!nbportef || !clientSelect) return;

           const val = clientSelect.value;
           if (!val) { nbportef.value = ""; return; }   // placeholder -> rien

           const opt = clientSelect.querySelector('option[value="' + val + '"]');
           nbportef.value = (opt && opt.getAttribute("data-nb")) || "";
        }

        // déclencheur : quand on choisit un titre, on charge les clients
        titreSelect.addEventListener("change", function () {
           chargerClients(this.value, null);
        });

        clientSelect.addEventListener("change", function () {
            alert('ok');
           const opt = this.options[this.selectedIndex];
           const nb  = opt ? opt.getAttribute("data-nb") : "";
           const nbportef = document.getElementById("id_nbportef");
           if (nbportef) nbportef.value = nb || "";
        });

        // Au changement de type
        typeSelect.addEventListener("change", function () {
            chargerTitres(this.value, null);
        });

		titreSelect.addEventListener("change", function () {
           chargerClients(this.value, null);
        });

		const dejaChoisi = titreSelect.getAttribute("data-selected") || "";
		if (typeSelect.value) {
			chargerTitres(typeSelect.value, dejaChoisi);
		}

	});
})();
