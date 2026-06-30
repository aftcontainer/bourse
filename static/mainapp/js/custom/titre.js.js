$(document).ready(function () {
            // --- DataTable + recherche ---
            var table = document.getElementById("kt_titre_table");
            var dt = $(table).DataTable({
                info: false,
                order: [],
                columnDefs: [
                    { orderable: false, targets: 0 },
                    { orderable: false, targets: 4 },
                ],
            });

            var filterSearch = document.querySelector('[data-kt-subscription-table-filter="search"]');
            if (filterSearch) {
                filterSearch.addEventListener("keyup", function (e) {
                    dt.search(e.target.value).draw();
                });
            }

            $(document).on("click", ".deleteBtn", function (e) {
                e.preventDefault();
                const id = $(this).data("id");
                const url = "/parametres/types-operations";

                Swal.fire({
                    text: "Voulez-vous vraiment supprimer cet type d'opération ?",
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