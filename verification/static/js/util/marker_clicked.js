function getCookie(name){
    var cookieValue=null;
    if(document.cookie&&document.cookie!=''){
        var cookies=document.cookie.split(';');
        for(var i=0;i<cookies.length;i++){
            var cookie=cookies[i].trim();
            //Does this cookie string begin with the name we want?
            if(cookie.substring(0,name.length+1)==(name+'=')){
                cookieValue=decodeURIComponent(cookie.substring(name.length+1));
                break;
            }
        }
    }
    return cookieValue;
}

export default function marker_clicked(eventObj) {
    $.ajax({
        type: "POST",
        url: '',
        data: {
            csrfmiddlewaretoken: getCookie('csrftoken'),
            meter_id: eventObj /*Passingthedata*/
        },
        success: function (json) {
            /*Youdon'thavetodoanythingheresincethedefchartfunctionisalreadyrerenderingthechart
            inthelinereturnrender(....).YoucoulddoanIFNOTPOSTREQUESTTHENRETURNJSONinsteadof
            returningtheentirerender.
            */
            console.log("it worked, here is what is being passed back from Python: " + json);
            FusionCharts.items["myChart"].setJSONData(json);
        },
        error: function () {
            console.log(eventObj)
        }
    });
}