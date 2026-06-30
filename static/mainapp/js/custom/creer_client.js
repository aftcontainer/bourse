$(document).ready(function () {
            // --- DataTable + recherche ---
            $("#id_category_client").on("change",function(){
                if($("#id_category_client").val()==='Personne physique résidente'){
                    alert($("#id_category_client").val());
                    $(".matri").show();
                    $(".div_date_naissance").show();$(".div_prenom_client").show();
                    $(".div_lieu_naissance").show();$(".div_nationalite").show();
                }else{
                    $(".matri").hide();
                    $(".div_date_naissance").hide();$(".div_prenom_client").hide();
                    $(".div_lieu_naissance").hide();$(".div_nationalite").hide();
                }
            });


        });