function checkCallStatus(deviceId){
    let body = {
      command: "call_status",
      device_id: deviceId
    }
    return $.post('/command', JSON.stringify(body)).done(function (response) {
      let jresp = JSON.parse(response);
      console.log('checkCallStatus:');
      console.log(jresp);
    });
}

function moveCamera(element, device_id){
    if(device_id){
      let body = {
        command: "move_camera",
        device_id: device_id,
        camera_id: parseInt(document.getElementById("cameras").value),
        direction: element.className
      }
      console.log(body);
      $.post('/command', JSON.stringify(body)).done(function (response) {
        let jresp = JSON.parse(response);
        if(jresp.data){
          updateSummary(`moveCamera - ${JSON.stringify(jresp.data)}`);
        } else {
          updateSummary(`moveCamera - HTTP ${jresp.code} Error: ${jresp.reason}`);
        }
      });
    } else {
      updateSummary(`moveCamera - Error: Device ID is null`)
    }
}

function setVolume(volume, device_id){
    let body = {
      command: "set_volume",
      device_id: device_id,
      volume : parseInt(volume)
    }
    return $.post('/command', JSON.stringify(body)).done(function (response) {
      let jresp = JSON.parse(response);
      console.log('setVolume:');
      console.log(jresp);
    });
}

function setMute(button, device_id){
    let mute = false;
    if($(button).hasClass('is-primary')){
    mute = true;
    }
    let body = {
    command: "set_mute",
    device_id: device_id,
    mute : mute
    }
    return $.post('/command', JSON.stringify(body)).done(function (response) {
    let jresp = JSON.parse(response);
    console.log('setMute:');
    console.log(jresp);
    });
}

function muteStyle(button){
    $(button).removeClass('is-primary');
    $(button).addClass('is-danger');
    $("#mute-icon").removeClass('fa-microphone');
    $("#mute-icon").addClass('fa-microphone-slash');
}

function unmuteStyle(button){
    $(button).addClass('is-primary');
    $(button).removeClass('is-danger');
    $("#mute-icon").addClass('fa-microphone');
    $("#mute-icon").removeClass('fa-microphone-slash');
}

function confirmMuteStyle(isUnmuted){
    if(isUnmuted){
    unmuteStyle($('#mute'));
    } else {
    muteStyle($('#mute'));
    }
}

function forceSwapMuteStyle(button){
    if($(button).hasClass('is-primary')){
    muteStyle(button);
    } else {
    unmuteStyle(button);
    }
}