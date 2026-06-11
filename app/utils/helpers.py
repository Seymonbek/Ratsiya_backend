def build_audio_url(message_id: int) -> str:
    
    return f"/api/v1/messages/{message_id}/audio"
