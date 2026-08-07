$(document).ready(function () {

    // --- DataTable + recherche ---
    let table = $('#kt_clients_table').DataTable({

        processing: true,
        serverSide: true,

        ajax: {
            url: "/clients/data",
            type: "GET"
        },

        pageLength: 10,

        columns: [
            { data: 0 },
            { data: 1 },
            { data: 2 },
            { data: 3 },
            { data: 4 },
            { data: 5 },
            { data: 6 }
        ],

        language: {
            search: "Recherche :",
            lengthMenu: "Afficher _MENU_ lignes",
            info: "Page _PAGE_ sur _PAGES_",
            paginate: {
                first: "Premier",
                last: "Dernier",
                next: "Suivant",
                previous: "Précédent"
            },
            processing: "" // texte masqué : l'overlay ci-dessous prend le relais
        }

    });

    // --- Overlay de chargement (branché sur l'événement natif de DataTable) ---
    // Se déclenche automatiquement au chargement initial, à la recherche,
    // au tri et à la pagination : pas besoin de le gérer manuellement.
    table.on('processing.dt', function (e, settings, processing) {
        $('#kt_clients_table_overlay')
            .toggleClass('d-none', !processing)
            .toggleClass('d-flex', !!processing);
    });

    // Recherche personnalisée
    $('#client_search').on('keyup', function () {
        table.search(this.value).draw();
    });

    $(".editBtn").on("click", function () {
        $("#editCatClientForm input[name='libelle']").val($(this).data("libelle"));
        $("#editCatClientForm input[name='id']").val($(this).data("id"));
    });

    $(document).on("click", ".deleteBtn", function (e) {
        e.preventDefault();
        const id = $(this).data("id");
        const url = "/parametres/categories-clients";

        Swal.fire({
            text: "Voulez-vous vraiment supprimer cette catégorie de client ?",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Oui, supprimer",
            cancelButtonText: "Annuler",
            buttonsStyling: false,
            customClass: {
                confirmButton: "btn btn-danger",
                cancelButton: "btn btn-light",
            },
        }).then(function (result) {
            if (!result.isConfirmed) return;

            $.ajax({
                type: "post",
                url: url,
                data: {
                    action: "delete",
                    id: id,
                    csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
                },
                success: function (response) { notifier(response["status"], response["msg"]); },
                error: function (xhr) {
                    var d = xhr.responseJSON || {};
                    notifier(d.status || "error", d.msg || "Une erreur s'est produite");
                },
            });
        });
    });

});