const queryString = window.location.search;
const urlParams   = new URLSearchParams(queryString);
const PATHNAME    = window.location.pathname
const VIEW        = urlParams.get('view');
const MARGIN_TOP  = urlParams.get('margin-top');

function redirectPage(redirectTo){
    for(let paramArr of urlParams){
        if(paramArr[0] != "returnTo"){
            redirectTo += `&${paramArr[0]}=${paramArr[1]}`;
        }
    }
    window.location = redirectTo;
}

function universalHeader(){
    if(MARGIN_TOP){
        $('#header-box').removeClass('mt-0');
        $('#header-box').addClass(`mt-${MARGIN_TOP}`);
    }

    if(VIEW == "instantconnect"){
        $('#main-title').text('Instant Connect with Far End Camera Control');
    }
}