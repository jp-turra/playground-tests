enum WRTC_SignalingChannelMessagesTypes {
    ICE_CANDIDATE = "ice_candidate",
    OFFER = "offer",
    ANSWER = "answer",
    CONFIGURE = "configure"
}

enum WRTC_ConfigureActionTypes {
    ADD_STREAM = "add_stream",
    REMOVE_STREAM = "remove_stream",
    ADD_VIDEO_TRACK = "add_video_track",
    ADD_AUDIO_TRACK = "add_audio_track",
    EXPECT_STREAM = "expect_stream",
    EXPECT_VIDEO_TRACK = "expect_video_track",
}

interface WRTC_IceCandidateMessageInterface {
    type: WRTC_SignalingChannelMessagesTypes.ICE_CANDIDATE
    sdp_mid: string
    sdp_mline_index: number
    candidate: string
}
  
interface WRTC_OfferMessageInterface {
    type: WRTC_SignalingChannelMessagesTypes.OFFER
    sdp: string
}
  
interface WRTC_ConfigureActionInterface {
    type: WRTC_ConfigureActionTypes
    id: string
    stream_id?: string
    src?: string
    dest?: string
}

interface WRTC_ConfigureMessageInterface {
    type: WRTC_SignalingChannelMessagesTypes.CONFIGURE
    actions?: Array<WRTC_ConfigureActionInterface>
}

export type {
    WRTC_IceCandidateMessageInterface,
    WRTC_OfferMessageInterface,
    WRTC_ConfigureActionInterface,
    WRTC_ConfigureMessageInterface
}

export {
    WRTC_SignalingChannelMessagesTypes,
    WRTC_ConfigureActionTypes
}