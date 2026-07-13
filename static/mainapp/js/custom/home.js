$(document).ready(function () {
    // Couleurs de la charte AFG
    var AFG = { blue:"#001051", green:"#22B14C", greenDark:"#17962f", red:"#ED1C24" };

    document.addEventListener("DOMContentLoaded", function () {
        if (typeof ApexCharts === "undefined") { return; } // ApexCharts est fourni par plugins.bundle.js

        /* ---------- Données de démonstration ----------
           Pour brancher les vraies données depuis la vue, utilisez json_script :
             dans le template :  {{ series_achats|json_script:"afg-achats" }}
             puis en JS       :  JSON.parse(document.getElementById('afg-achats').textContent)
        */
        var categories = ["S1","S2","S3","S4","S5","S6","S7","S8","S9","S10","S11","S12"];
        var achats = [31,40,28,51,42,60,55,48,62,58,70,65];
        var ventes = [22,30,25,38,34,40,36,44,39,48,45,52];

        // --- Graphique évolution des opérations (aires) ---
        new ApexCharts(document.querySelector("#afg_chart_operations"), {
            chart:{ type:"area", height:320, toolbar:{show:false}, fontFamily:"inherit" },
            series:[
                { name:"Achats", data:achats },
                { name:"Ventes", data:ventes }
            ],
            colors:[AFG.green, AFG.red],
            dataLabels:{ enabled:false },
            stroke:{ curve:"smooth", width:3 },
            fill:{ type:"gradient", gradient:{ shadeIntensity:1, opacityFrom:0.35, opacityTo:0.05, stops:[0,90,100] } },
            xaxis:{ categories:categories, axisBorder:{show:false}, axisTicks:{show:false}, labels:{ style:{ colors:"#a1a5b7" } } },
            yaxis:{ labels:{ style:{ colors:"#a1a5b7" } } },
            grid:{ borderColor:"#eff2f5", strokeDashArray:4 },
            legend:{ show:false },
            tooltip:{ theme:"light" }
        }).render();

        // --- Graphique répartition des titres (donut) ---
        new ApexCharts(document.querySelector("#afg_chart_titres"), {
            chart:{ type:"donut", height:230, fontFamily:"inherit" },
            series:[52, 31, 17],
            labels:["Actions","Obligations","Autres"],
            colors:[AFG.blue, AFG.green, AFG.red],
            stroke:{ width:2 },
            dataLabels:{ enabled:false },
            legend:{ show:false },
            plotOptions:{ pie:{ donut:{ size:"68%", labels:{ show:true,
                total:{ show:true, label:"Titres", fontWeight:600, color:"#7e8299",
                    formatter:function(){ return "{{ nb_titres|default:'128' }}"; } } } } } }
        }).render();
    });
});