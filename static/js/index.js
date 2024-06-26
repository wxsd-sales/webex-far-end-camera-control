var IC_CONVERSATION_ID;
var IC_DETAILS;
var MEETING_ID;
var DEVICE_ID;
var DECODED_DEVICE_ID;
var myDevices;
var myMeetings;

function deviceMatch(deviceUrl, decodedDevice){
  return typeof(deviceUrl) == "string" && deviceUrl.indexOf(decodedDevice) >= 0
}

function getDecodedDeviceId(deviceId){
  let temp = window.atob(deviceId);
  return temp.split('/DEVICE/')[1].trim();
}

function setDeviceId(deviceId){
  DEVICE_ID = deviceId;
  DECODED_DEVICE_ID = getDecodedDeviceId(deviceId);
}

function clearDevice(){
  if(DEVICE_ID){
    myDevices[DEVICE_ID]["meeting_member_id"] = undefined;
    myDevices[DEVICE_ID]["in_meeting"] = false;
  }
  DEVICE_ID = undefined;
  DECODED_DEVICE_ID = undefined;
  $('.clear-device').removeClass('is-loading');
  $('.clear-device').prop('disabled', true);
  $("#dial-device").removeClass('is-loading');
  $("#dial-device").prop('disabled', false);
  $("#dial-devices").prop('disabled', false);
  $("#cameras-div").hide();
}

function setDeviceInMeeting(member){
  $("#dial-device").prop('disabled', true);
  $("#dial-devices").prop('disabled',true);
  myDevices[DEVICE_ID]["in_meeting"] = true;
  myDevices[DEVICE_ID]["meeting_member_id"] = member.id;
  $('.clear-device').prop('disabled', false);
  $("#dial-device").removeClass('is-loading');
  deviceStatus(DEVICE_ID);
}

function clearMeeting(){
  //$(`#leave_${MEETING_ID}`).css('visibility', 'hidden');
  $(`#reset-div`).hide();
  $('#dial-devices-div').hide();
  updateSummary(`Cleared MeetingId - ${MEETING_ID}`);
  MEETING_ID = undefined;
  clearDevice();
  $(`.meeting-button`).prop('disabled',false);
}


function addMeeting(event){
  console.log('meeting:added event');
  let conversationUrl = event.meeting.conversationUrl;
  console.log(conversationUrl);
  if( isController || (typeof(conversationUrl) == "string" && conversationUrl.indexOf(IC_CONVERSATION_ID) >= 0) ){
    $("#no-meetings").hide();
    console.log(event);
    let name = event.meeting.meetingInfo.meetingName;
    if(!name){
      name = name = event.meeting.meetingInfo.topic;
      if(!name){
        name = event.meeting.partner.person.name;
      }
      
    }
    buttonControl = "";
    if(IC_CONVERSATION_ID){
      buttonControl = "disabled"; 
      MEETING_ID = event.meeting.id;
      if(VIEW == "telehealth"){
        $('#dial-telehealth-div').show();
      } else {
        $('#dial-devices-div').show();
      }
    }

    showControls();

    $("#my-meetings").append(
      $(`<div id="mtg_${event.meeting.id}" class="columns is-centered"/>`).append(
        //$('<div class="column is-1 is-centered py-0">'),
        $('<div class="column is-centered"/>').append(
          $(`<button id="${event.meeting.id}" class="button meeting-button is-primary" ${buttonControl}/>`).text(name).on('click', function(e){
            $('.meeting-button').prop('disabled', true);
            if(MEETING_ID){
              clearMeeting();
            }
            MEETING_ID = this.id;
            updateSummary(`Using MeetingId - ${MEETING_ID}`);
            //$(`#leave_${event.meeting.id}`).css('visibility', 'visible');
            $(`#reset-div`).show();
            if(VIEW == "telehealth"){
              $('#dial-telehealth-div').show();
            } else {
              $('#dial-devices-div').show();
            }
          })
        )
      )
    );
    
    console.log('listening to member changes for meeting:');
    console.log(event.meeting);
    event.meeting.members.on('members:update', (payload) => {
      try{
        console.log("<members:update>", payload);
        for(let updated of payload.delta.updated){
          if(updated.isDevice){
            let deviceUrl = updated.participant.deviceUrl;
            console.log(`deviceUrl - ${deviceUrl}`);
            console.log(updated.status);
            if(updated.status == "IN_MEETING" && deviceMatch(deviceUrl, DECODED_DEVICE_ID)){
              if( !myDevices[DEVICE_ID]["in_meeting"] ){
                updateSummary(`${myDevices[DEVICE_ID].name} joined meeting.`);
                setDeviceInMeeting(updated);
              } else {
                  console.log('Device already in meeting.');
              }
              if(updated.isAudioMuted !== undefined){
                let isUnmuted = !updated.isAudioMuted;
                confirmMuteStyle(isUnmuted);
              }
            } else if(updated.status == "NOT_IN_MEETING" && myDevices[DEVICE_ID]["meeting_member_id"] == updated.id) {
              updateSummary(`${myDevices[DEVICE_ID].name} left meeting.`);
              clearDevice();
            }
          }
        }
      } catch (e){
        console.log('members.on(members:update) - error:');
        console.log(e);
      }
    });
  }
}

function removeMeeting(event){
  console.log('meeting:removed event');
  console.log(event);
  updateSummary(`MeetingId - ${event.meetingId} has ended.`);
  $(`#mtg_${event.meetingId}`).remove();
  if(event.meetingId == MEETING_ID){
    clearMeeting();
  }
  if(Object.keys(myMeetings).length == 0){
    $("#no-meetings").show();
  }
}


function updateSummary(response){
  var today = new Date();
  var time = ('0' + today.getHours()).substr(-2) + ":" + ('0' + today.getMinutes()).substr(-2) + ":" + ('0' + today.getSeconds()).substr(-2);
  text = time + " - " + response;
  var summary_area = document.getElementById("summary");
  summary_area.value = text + "\n" + summary_area.value;
  summary_area.scrollTop = 0;
}


function listDevices(){
  $.post('/command', JSON.stringify({command: "list_devices"})).done(function (response) {
    console.log(response);
    let jresp = JSON.parse(response);
    if(jresp.data){
      myDevices = jresp.data;
      for(let deviceId of Object.keys(jresp.data)){
        let device = jresp.data[deviceId];
        let ele = $(`<option value="${deviceId}">${device.name}</option>`);
        $("#dial-devices").append(ele);
        $("#set-devices").append(ele.clone());
      }
    } else {
      console.log(`listDevices - returned ${jresp.data}`);
    }
  });
}


function deviceStatus(deviceId){
    updateSummary('deviceStatus - Loading...');
    $("#cameras").empty();
    let body = {
        command : "device_status",
        device_id : deviceId
    }
    console.log(body);
    $.post('/command', JSON.stringify(body)).done(function (response) {
      console.log(response);
      let jresp = JSON.parse(response);
      if(jresp.data && jresp.data.cameras){
        for(let camera of jresp.data.cameras){
          console.log(camera)
          if(camera.Connected.toLowerCase() == "true"){
            $("#cameras").append(
              $(`<option value="${camera.id}">Camera ${camera.id}</option>`)
            )
          }
        }

        $("#cameras").on('change', function (e) {
          let body = {
            command: "set_main_video_source",
            device_id: DEVICE_ID,
            source_id: parseInt(this.value),
          }
          $.post('/command', JSON.stringify(body)).done(function (response) {
            console.log(response);
          });
        });
      
        if(jresp.data.source){
          $("#cameras").val(jresp.data.source);
        }

        if(typeof(jresp.data.microphones) == "object" && jresp.data.microphones.length > 0){
          let isUnmuted = jresp.data.microphones[0]["Mute"].toLowerCase() == "off";
          confirmMuteStyle(isUnmuted);
        }

        if(typeof(jresp.data.volume) == "number"){
          $("#volume-text").text(jresp.data.volume);
          $("#volume-slider").val(jresp.data.volume);
        }

        updateSummary(`deviceStatus - Success`);
        $("#cameras-div").show();
      } else {
        updateSummary(`deviceStatus - HTTP ${jresp.code} Error: ${jresp.reason}`);
        $("#cameras-div").hide();
      }
    }); 
}


function showControls(){
  $('#controls-loading').hide();
  $('#main-controls').show();
  $('#load-meeting').removeClass('is-loading');
}


function showInstantConnectMeeting(url){
  $("#hero-section").removeClass('has-background-grey-light');
  $("#hero-content").append(
    $(`<iframe src="${url}" allow="camera;microphone;">`).on("load", function() {
      $('#loading-notification').text("Please join the consultation when it's available.")
    })
  )
}

function startInstantConnectMeeting(details){
  let body = {command: "start_meeting", details:details};
  $.post('/command', JSON.stringify(body)).done(function (response) {
    console.log(response);
    let jresp = JSON.parse(response);
    if(jresp.data){
      IC_CONVERSATION_ID = jresp.data["conversationId"];
      IC_DETAILS = jresp.data["details"];
      showInstantConnectMeeting(jresp.data["url"]);
    } else {
      console.log('startInstantConnectMeeting - failed');
    }
  });
}

function resetDialer(){
  $("#dial-device").removeClass('is-loading');
  $("#dial-devices").prop('disabled',false);
}

function deviceInMeeting(deviceId, meeting){
  let decodedDevice = getDecodedDeviceId(deviceId);
  for(let memberId of Object.keys(meeting.members.membersCollection.members)){
    let member = meeting.members.membersCollection.members[memberId];
    if(member.isDevice && deviceMatch(member.participant.deviceUrl, decodedDevice)){
      updateSummary(`Device already in meeting. You may now control the device.`);
      setDeviceId(deviceId);
      setDeviceInMeeting(member);
      return true;
    }
  }
  return false
}


function deviceIsAvailable(data){
  return typeof(data) == "object" && data.length == 0
}

function pollCallStatus(deviceId){
  let freqSeconds = 7;
  let counter = 0
  let maxAttempts = 5
  let statusInterval = setInterval(checkStatus, 1000 * freqSeconds);
  function checkStatus(){
    checkCallStatus(deviceId).then((response) => {
      let jresp = JSON.parse(response);
      console.log(`pollCallStatus: ${counter}`);
      if(typeof(jresp.data) == "object" && jresp.data[0] && jresp.data[0]["Status"].toLowerCase() == "ringing"){
        updateSummary(`pollCallStatus - Device is ringing...`);
      } else {
        clearInterval(statusInterval);
        resetDialer();
        if(deviceIsAvailable(jresp.data)){
          updateSummary(`checkCallStatus - Device declined or missed the call.`);
        } else {
          if(!myDevices[DEVICE_ID]["in_meeting"]){
            updateSummaryCallStatus(jresp);
          }
        }
      }
      if(counter >= maxAttempts){
        clearInterval(statusInterval);
        resetDialer();
      }
      counter += 1;
    });
  }
}

function updateSummaryCallStatus(jresp, unavailable){
  let message = `Device's call status is`;
  if(unavailable){
    message = `Device is not available. It's call status is`;
  }
  if(typeof(jresp.data) == "object" && jresp.data.length > 0){
    updateSummary(`checkCallStatus - ${message} '${jresp.data[0]["Status"]}'.`);
  } else {
    updateSummary(`checkCallStatus - HTTP ${jresp.code} Error: ${jresp.reason}`);
  }
}


$('document').ready(function() {
  
  if(VIEW != "telehealth"){
    listDevices();
  }

  webex.meetings.on('meeting:added', (event) => {
    addMeeting(event);
  })
  webex.meetings.on('meeting:removed', (event) => {
    removeMeeting(event);
  });

  myMeetings = webex.meetings.meetingCollection.meetings;
  webex.meetings.syncMeetings();
  console.log(myMeetings);

  $('#webex-avatar').attr('src', webexAvatar);

  $("#dial-telehealth").on('click', function(e) {
    console.log(e);
    let meeting = webex.meetings.meetingCollection.meetings[MEETING_ID];
    console.log('dial-telehealth - meeting:');
    console.log(meeting);
    if(meeting){
      $("#dial-telehealth").addClass('is-loading');
      $("#dial-telehealth").prop('disabled',true);
      let body = {
        command: "dial_telehealth",
        details: IC_DETAILS
      }
      setTimeout(function(){
        $("#dial-telehealth").removeClass('is-loading');
        $("#dial-telehealth").prop('disabled',false);
      }, 1000 * 20);
      $.post('/command', JSON.stringify(body)).done(function (response) {
        let jresp = JSON.parse(response);
        console.log('dial_telehealth done response:');
        console.log(jresp);
      });
    } else {
      updateSummary(`Dial Error - You must select a meeting first.`);
    }
  });

  $("#dial-device").on('click', function(e) {
    console.log(e);
    let deviceId = document.getElementById("dial-devices").value;
    let meeting = webex.meetings.meetingCollection.meetings[MEETING_ID];
    let sip = myDevices[deviceId].sip;
    console.log('dial-device - meeting:');
    console.log(meeting);
    console.log(`dial-device - sip:${sip}`)
    if(meeting){
      $("#dial-device").addClass('is-loading');
      $("#dial-devices").prop('disabled',true);
      if(!deviceInMeeting(deviceId, meeting)){
        setDeviceId(deviceId);
        checkCallStatus(deviceId).then((response) => {
          let jresp = JSON.parse(response);
          if(deviceIsAvailable(jresp.data)){
            meeting.invite({"email":sip}).then((res) => {
              updateSummary(`Dialing - ${sip}`);
              console.log('meeting.invite result:')
              console.log(res);
              pollCallStatus(deviceId);
            }).catch((err) => {
              updateSummary(`Dial Error - ${err}`);
              resetDialer();
            });
          } else {
            updateSummaryCallStatus(jresp, true);
            resetDialer();
          }
        });
      }
    } else {
      updateSummary(`Dial Error - You must select a meeting first.`);
    }
  });

  $('.clear-device').on('click', function(e) {
    let meeting = webex.meetings.meetingCollection.meetings[MEETING_ID];
    meeting.remove(myDevices[DEVICE_ID]["meeting_member_id"]);
    $('.clear-device').addClass('is-loading');
  });


  $("#start-meeting").on('click', function(e) {
    $(e.target).addClass('is-loading');
    $('#loading-notification').css('visibility', 'visible');
    let details = false;
    if(VIEW == "telehealth"){
      details = true;
    }
    startInstantConnectMeeting(details);
  });

  $("#reset-meeting").on('click', function(e) {
    console.log('clicked');
    clearMeeting();
  });

  var slider = document.getElementById("volume-slider");
  //var output = document.getElementById("demo");
  //output.innerHTML = slider.value; // Display the default slider value

  // Update the current slider value (each time you drag the slider handle)
  slider.onchange = function() {
    console.log(this.value);
    $("#volume-text").text(this.value);
    setVolume(this.value, DEVICE_ID);
  } 

  slider.oninput = function() {
    $("#volume-text").text(this.value);
  }

  $('#mute').on('click', function(e){
    setMute(this, DEVICE_ID);
    forceSwapMuteStyle(this);
  })

  $('#zoom-in').on('click', function(e){
    let element = {className : "in"};
    moveCamera(element, DEVICE_ID);
  })

  $('#zoom-out').on('click', function(e){
    let element = {className : "out"};
    moveCamera(element, DEVICE_ID);
  })

  $('.up, .right, .down, .left').on('click', function(e){
    console.log(this);
    moveCamera(this, DEVICE_ID);
  })

  $('#logout').on('click', function(e){
    let redirectTo = "/logout?";
    let returnTo = PATHNAME;
    returnTo = returnTo.replace("/", "");
    if(returnTo != ""){
      redirectTo += `returnTo=${returnTo}&`;
    }
    redirectTo += window.location.search.replace("?","");
    window.location = redirectTo;
  })

})
