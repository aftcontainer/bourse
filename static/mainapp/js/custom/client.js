$(document).ready(function () {
            // --- DataTable + recherche ---
            var table = document.getElementById("kt_clients_table");
            var dt = $(table).DataTable({
                info: false,
                order: [],
                columnDefs: [
                    { orderable: false, targets: 0 },
                    { orderable: false, targets: 5 },
                ],
            });

            var filterSearch = document.querySelector('[data-kt-subscription-table-filter="search"]');
            if (filterSearch) {
                filterSearch.addEventListener("keyup", function (e) {
                    dt.search(e.target.value).draw();
                });
            }

            $(".editBtn").on("click", function(){
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