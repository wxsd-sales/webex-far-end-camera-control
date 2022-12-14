# Far End Camera Control
<a href="https://fecc.wbx.ninja/?view=instantconnect"><strong>View Instant Connect Demo</strong></a>
·
<a href="https://fecc.wbx.ninja/"><strong>View Controller Demo</strong></a>
·
<a href="https://github.com/WXSD-Sales/webex-far-end-camera-control/issues"><strong>Report Bug</strong></a>
·
<a href="https://github.com/WXSD-Sales/webex-far-end-camera-control/issues"><strong>Request Feature</strong></a>

This is a Web App which can control Pan/Tilt/Zoom (PTZ) functions of applicable Webex Devices. It works purely through the Cloud xAPI, using the token of a bot that has been added to the shared device's Workspace in Control Hub.

## Overview
[![PTZ/FECC Video](https://user-images.githubusercontent.com/19175490/192361294-15d31319-d14d-4412-a4a7-9106473dc681.png)](https://app.vidcast.io/share/c4e04b00-22e7-4f4e-b34a-94ac46437c53)

Server Requirements:
1. python version >= 3.8
2. pip install modules.


## Setup

### Server Side Setup
1. Clone this repository
2. Rename ```sample.env``` to ```.env```, and edit the values in .env *(be sure to keep string values between the quotes)*
3. Navigate inside the cloned directory in your terminal, then run:
```
pip install python-dotenv
pip install tornado==4.5.2
pip install requests
pip install requests-toolbelt
```

## Usage

### Instant Connect Demo
1. For the Instant Connect Demo, you can simply click start.  
2. Permissions are limited to CEC credentials in the live version.  
3. Once your meeting has been joined, you can dial a registered device.  
4. Once the device has answered the call, you can control its PTZ functions.  

### Controller Demo
1. For the Controller Demo, you will need to be in an active meeting using your Webex client.  
2. You will be able to select a meeting you are currently a member of.  
3. You can dial a device (assuming you have permission).  
4. You can control the device once it has answered the invite call.  


## Support

Please reach out to the WXSD team at [wxsd@external.cisco.com](mailto:wxsd@external.cisco.com?cc=<your_cec>@cisco.com&subject=RepoName).
