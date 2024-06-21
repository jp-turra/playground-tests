"use client"

import { useState } from "react";
import Header from "@/components/header";
import {
  WRTC_ConfigureActionTypes, 
  WRTC_SignalingChannelMessagesTypes,
  WRTC_ConfigureActionInterface,
  WRTC_ConfigureMessageInterface,
  WRTC_IceCandidateMessageInterface,
  WRTC_OfferMessageInterface
} from "@/interfaces/webrtc-interfaces";

const rtcPeerConfiguration = {
  'iceServers': [
    {'urls': 'stun:stun.l.google.com:19302'}
  ]
}

const MEDIA_CONSTRAINTS = {
  "optional": [
    {"OfferToReceiveAudio": true},
  ]
}

const WEBSOCKET_URL = "ws://localhost:8508/webrtc"
const CAMERA_TOPIC = "/rover/stream/image_raw"

interface StramsCallbackInterface {
  [key: string]: {
    resolve: Function,
    reject: Function
  }
}

interface StreamInterface {
  id: string
  src: string
}

interface BothStreamInterface {
  video: StreamInterface

  audio?: StreamInterface
}

class SignalingChannel extends WebSocket {
  peerConnection: RTCPeerConnection | undefined
  onConfigurationNeeded: Function | undefined = undefined
  addStreamCallbacks: StramsCallbackInterface = {}
  removeTrackCallbacks: StramsCallbackInterface = {}
  lastConfigureActionPromise: Promise<Array<WRTC_ConfigureActionInterface>> = Promise.resolve([])

  constructor(url: string, protocol?: string | string[] | undefined) {
    super(url, protocol);
  }

  connect() {
    this.onmessage = this.onSignalingMessage
    this.onopen = this.onConnectionOpen
    this.onerror = this.onSignalingError
    this.onclose = this.onSignalingClose

    this.peerConnection = new RTCPeerConnection(rtcPeerConfiguration)
    this.peerConnection.onicecandidate = this.onIceCandidate.bind(this)
    this.peerConnection.ontrack = this.onReceivedStream.bind(this)
  }

  sendSignalingAnswer() {
    const self = this

    if (!this.peerConnection) {
      console.error("[sendSignalingAnswer] peerConnection is undefined")
      return
    }

    this.peerConnection.createAnswer(MEDIA_CONSTRAINTS)
      .then((sessionDescription: RTCSessionDescriptionInit) => {
        if (!self.peerConnection) {
          console.error("[sendSignalingAnswer] peerConnection is undefined.")
          return
        }
        self.peerConnection.setLocalDescription(sessionDescription)
        self.send(
          JSON.stringify(sessionDescription)
        )
      })
      .catch((error: DOMException) => {
        console.error("[sendSignalingAnswer] createAnswer", error)
      })
  }
  
  onSignalingMessage(event: MessageEvent<any>) {
    const dataJson = JSON.parse(event.data)
    const self = this

    if (dataJson.type === WRTC_SignalingChannelMessagesTypes.OFFER) {
      console.log("Received WebRTC Offer via WebRTC signaling channel")

      if (!this.peerConnection) {
        console.error("onSignalingMessage: peerConnection is undefined")
        return
      }

      this.peerConnection.setRemoteDescription(new RTCSessionDescription(dataJson))
        .then(() => {self.sendSignalingAnswer()})
        .catch((event: DOMException) => {console.error("onRemoteSdpError", event)})
    }
  }

  onConnectionOpen() {
    console.log("WebRTC signaling connection established");
    if (this.onConfigurationNeeded) {
      this.onConfigurationNeeded();
    }
  }

  onSignalingError() {
    console.log("WebRTC signaling error");
  }

  onSignalingClose() {
    console.log("WebRTC signaling closed");
  }

  onIceCandidate(event: RTCPeerConnectionIceEvent) {
    if (event.candidate) {
      const cadidate: WRTC_IceCandidateMessageInterface = {
        type: WRTC_SignalingChannelMessagesTypes.ICE_CANDIDATE,
        sdp_mid: event.candidate.sdpMid ? event.candidate.sdpMid : "",
        sdp_mline_index: event.candidate.sdpMLineIndex ? event.candidate.sdpMLineIndex : 0,
        candidate: event.candidate.candidate
      }

      this.send(
        JSON.stringify(cadidate)
      )
    }
  }

  onReceivedStream(event: RTCTrackEvent) {
    const self = this

    const addCallbackData = this.addStreamCallbacks[event.streams[0].id]
    if (addCallbackData) {
      event.streams[0].onremovetrack = function(event: MediaStreamTrackEvent) {
        const rmCallbackData = self.removeTrackCallbacks[event.track.id]
        if (rmCallbackData) {
          rmCallbackData.resolve({
            "track": event.track
          })
        }
      }

      addCallbackData.resolve({
        "stream": event.streams[0],
        "remove": new Promise((resolve, reject) => {
          self.removeTrackCallbacks[event.track.id] = {
            "resolve": resolve,
            "reject": reject
          }
        })
      })
    }

  }

  generateStreamId(): string {
		return "webrtc-stream-"+Math.floor(Math.random()*1000000000).toString();
	};

  addRemoteStream(config: BothStreamInterface): Promise<{stream: any, remove: any}> {
    const self = this
    const stream_id = this.generateStreamId()

    this.lastConfigureActionPromise = this.lastConfigureActionPromise.then(
			function(actions: Array<WRTC_ConfigureActionInterface>) {
				actions.push({
          type: WRTC_ConfigureActionTypes.ADD_STREAM, 
          id: stream_id
        })

				if(config.video) {
					actions.push({
						type: WRTC_ConfigureActionTypes.ADD_VIDEO_TRACK,
						stream_id: stream_id,
						id: stream_id + "/" + config.video.id,
						src: config.video.src
					});
				}

				if(config.audio) {
					actions.push({
						type: WRTC_ConfigureActionTypes.ADD_AUDIO_TRACK,
						stream_id: stream_id,
						id: stream_id + "/" + config.audio.id,
						src: config.audio.src
					});
				}

				return actions;
			}
		);

		return new Promise(function(resolve, reject) {
			self.addStreamCallbacks[stream_id] = {
				"resolve": resolve,
				"reject": reject
			};
		});
  }

  removeRemoteStream(stream: StreamInterface) {
    this.lastConfigureActionPromise = this.lastConfigureActionPromise.then(
    function(actions: Array<WRTC_ConfigureActionInterface>) {
      actions.push({
        type: WRTC_ConfigureActionTypes.REMOVE_STREAM, 
        id: stream.id
      })
      return actions
    }
    )
  }

  sendConfigure() {
    const self = this

    var currentLastConfigureActionPromise = this.lastConfigureActionPromise;
    this.lastConfigureActionPromise = Promise.resolve([])

    currentLastConfigureActionPromise.then(
      function(actions: Array<WRTC_ConfigureActionInterface>) {
        const message: WRTC_ConfigureMessageInterface = {
          type: WRTC_SignalingChannelMessagesTypes.CONFIGURE,
          actions: actions
        }

        self.send(JSON.stringify(message))
        console.log("WebRTC Configure: ", actions);
      }
    )
  }

  closeAll() {
    if (this.peerConnection) {
      this.peerConnection.close()
      this.peerConnection = undefined
    }

    if (this.CONNECTING == this.readyState || this.CLOSED == this.readyState) {
      this.close()
    }
  }

}

export default function Home() {
  const [serverConnected, setServerConnected] = useState(false);
  const [serverConnecting, setServerConnecting] = useState(false);

  function connectToWebRtcServer() {
    let signalingChannel = new SignalingChannel(WEBSOCKET_URL)

    if (serverConnected) {
      signalingChannel.closeAll()

      let video_element: HTMLVideoElement = document.getElementById("remote_video") as HTMLVideoElement
      video_element.srcObject = null

      setServerConnected(false)
      setServerConnecting(false)
      return
    }

    signalingChannel.onConfigurationNeeded = function() {
      console.log("Requesting WebRTC video subscription")
      let config: BothStreamInterface = {
        video: {
          id: "video",
          src: "ros_image:"+CAMERA_TOPIC
        }
      }

      signalingChannel.addRemoteStream(config)
        .then(function(event: any) {
          console.log("Connecting WebRTC stream to <video> element");
          (document.getElementById("remote_video") as HTMLVideoElement).srcObject = event.stream;
          setServerConnected(true);
          setServerConnecting(false);
          
          event.remove.then(function(event: any) {
            console.log("Disconnecting WebRTC stream from <video> element");
					  (document.getElementById("remote_video") as HTMLVideoElement).srcObject = null;
            setServerConnected(false);
          })
        })
        .catch(function(error: any) {
          console.log("[addRemoteStream] onError: ", error);
        })
      
      signalingChannel.sendConfigure()
    }
    setServerConnecting(true)
    signalingChannel.connect()
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
      <Header title="Next.js with WebRTC" />

      <button onClick={connectToWebRtcServer} disabled={serverConnecting}> {serverConnected ? "Disconnect" : "Connect"} to WebRTC Server </button>

      <div>
        <span>Server state: {serverConnected ? "Connected" : serverConnecting ? "Connecting" : "Disconnected"}</span>
      </div>

      <div>
        <video id="remote_video" autoPlay={true} style={{ width: "640px", height: "480px" }}></video>
      </div>
    </div>
  );
}
