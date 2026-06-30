function notifier(typeNotif,msg){
    notif({
        type: typeNotif,
        msg: msg,
        position: "center",
        opacity: 0.8
    });
    if(typeNotif==="success"){
        setTimeout(function(){
            location.reload();
        }, 2000);
    }
}
