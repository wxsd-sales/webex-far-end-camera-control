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

## Setup

### Prerequisites & Dependencies: 

Server Requirements:
1. python version >= 3.8
2. pip install modules.

### Local Installation:
1. Clone this repository
2. Rename ```sample.env``` to ```.env```, and edit the values in .env *(be sure to keep string values between the quotes)*
3. Navigate inside the cloned directory in your terminal, then run:
```
pip install python-dotenv
pip install tornado==4.5.2
pip install requests
pip install requests-toolbelt
```

### Glitch.com Installation:
You can setup this project on Glitch!  First, navigate to https://glitch.com, then select New Project.  
Click the ```Import from GitHub``` button at the bottom of the list.
![Screenshot 2023-05-16 at 9 30 24 AM](https://github.com/wxsd-sales/webex-far-end-camera-control/assets/19175490/3a161a59-9c40-4723-94fd-0018b0bd1fdb)  
Enter ```https://github.com/wxsd-sales/webex-far-end-camera-control.git``` in the text input and click OK.

Once you've cloned the project, you will need to  
1. Rename the file ```sample.env``` to simply ```.env``` in the Glitch project.
2. [Create a bot](https://developer.webex.com/my-apps/new/bot).  
    a. Save the bot token as ```MY_BOT_TOKEN``` in the .env file in Glitch.  
    b. In Control Hub, you will need to add this bot to every workspace that contains a device with 1 or more PTZ cameras.  
    c. As an admin, login to https://admin.webex.com.  Navigate to the desired workspaces. Click Edit API Access.  
    d. Search for the name of the bot you just created and give it Full Admin capabilities.  
3. [Create an integration](https://developer.webex.com/my-apps/new/integration).  
    a. The redirect URI of the integration must be https://your-glitch-project.glitch.me/webex-oauth, where ```your-glitch-project``` is replaced by your Glitch.com project name.  
    b. The Scopes selected must be:  
       meeting:schedules_read  
       meeting:preferences_read  
       meeting:controls_read  
       meeting:participants_read  
       spark:all  
    c. All other fields, like name, icon and description can be anything you choose.  
    d. Save the client_id, and client_secret as ```MY_WEBEX_CLIENT_ID``` and ```MY_WEBEX_SECRET``` in the .env file in Glitch respectively.  
    e. Save the redirect URI that you used in the Webex Integration as ```MY_WEBEX_REDIRECT_URI``` in the .env file.  
4. Retrieve your API Org Id from [here](https://developer.webex.com/docs/api/v1/organizations/list-organizations) and enter the value as ```MY_ORG_ID``` in the .env file.  
5. Enter one or more user email addresses, separated by commas as ```MY_USERS``` in the .env file.  These users should belong to the same org as ```MY_ORG_ID``` and will be allowed to sign in and use this application.  
6. It is recommended that you change ```MY_COOKIE_SECRET``` to a random alphabetical character string.  
7. You do not need to change any other variables in the .env file.  
8. You can test the app by click Preview at the bottom, and selecting Open in New Window.  
![Screenshot 2023-05-16 at 9 53 40 AM](https://github.com/wxsd-sales/webex-far-end-camera-control/assets/19175490/86cf713a-2da0-4649-8270-7ce14250b4e6)


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


## License
All contents are licensed under the MIT license. Please see [license](LICENSE) for details.

## Disclaimer
<!-- Keep the following here -->  
 Everything included is for demo and Proof of Concept purposes only. Use of the site is solely at your own risk. This site may contain links to third party content, which we do not warrant, endorse, or assume liability for. These demos are for Cisco Webex usecases, but are not Official Cisco Webex Branded demos.


## Support

Please reach out to the WXSD team at [wxsd@external.cisco.com](mailto:wxsd@external.cisco.com?cc=<your_cec>@cisco.com&subject=RepoName).
