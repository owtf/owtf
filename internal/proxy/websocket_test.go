package proxy

import (
	"encoding/base64"
	"encoding/json"
	"testing"
)

func TestWebSocketCaptureParsesMaskedAndUnmaskedFrames(t *testing.T) {
	capture := newWebSocketCapture(4096)
	client := capture.stream("client_to_server", true)
	server := capture.stream("server_to_client", false)
	masked := maskedFrame(1, []byte("hello"), [4]byte{1, 2, 3, 4})
	for _, part := range [][]byte{masked[:1], masked[1:4], masked[4:]} {
		if _, err := client.Write(part); err != nil {
			t.Fatal(err)
		}
	}
	_, _ = server.Write([]byte{0x82, 0x02, 0x00, 0xff})
	client.Close()
	server.Close()

	var transcript webSocketTranscript
	if err := json.Unmarshal(capture.bytes(), &transcript); err != nil {
		t.Fatal(err)
	}
	if len(transcript.Frames) != 2 {
		t.Fatalf("frames = %+v", transcript.Frames)
	}
	frames := make(map[string]webSocketFrame)
	for _, frame := range transcript.Frames {
		frames[frame.Direction] = frame
	}
	clientPayload, _ := base64.StdEncoding.DecodeString(frames["client_to_server"].PayloadBase64)
	serverPayload, _ := base64.StdEncoding.DecodeString(frames["server_to_client"].PayloadBase64)
	if string(clientPayload) != "hello" || frames["client_to_server"].Opcode != 1 || !frames["client_to_server"].Masked {
		t.Fatalf("client frame = %+v, payload = %q", frames["client_to_server"], clientPayload)
	}
	if string(serverPayload) != string([]byte{0x00, 0xff}) || frames["server_to_client"].Opcode != 2 || frames["server_to_client"].Masked {
		t.Fatalf("server frame = %+v, payload = %v", frames["server_to_client"], serverPayload)
	}
}

func TestWebSocketCaptureMarksProtocolErrorsAndIncompleteFrames(t *testing.T) {
	capture := newWebSocketCapture(4096)
	client := capture.stream("client_to_server", true)
	_, _ = client.Write([]byte{0x09, 0x00})
	_, _ = client.Write([]byte{0x81, 0x03, 'x'})
	client.Close()

	var transcript webSocketTranscript
	if err := json.Unmarshal(capture.bytes(), &transcript); err != nil {
		t.Fatal(err)
	}
	if len(transcript.Frames) != 2 || transcript.Frames[0].ProtocolError == "" || transcript.Frames[1].ProtocolError == "" {
		t.Fatalf("frames = %+v", transcript.Frames)
	}
}

func TestWebSocketTranscriptHonorsBodyBound(t *testing.T) {
	capture := newWebSocketCapture(256)
	server := capture.stream("server_to_client", false)
	for index := 0; index < 10; index++ {
		_, _ = server.Write(append([]byte{0x82, 100}, make([]byte, 100)...))
	}
	server.Close()
	data := capture.bytes()
	if len(data) > 256 || !json.Valid(data) {
		t.Fatalf("transcript length = %d, valid = %t", len(data), json.Valid(data))
	}
	var transcript webSocketTranscript
	_ = json.Unmarshal(data, &transcript)
	if !transcript.Truncated {
		t.Fatalf("bounded transcript was not marked truncated: %+v", transcript)
	}
}

func maskedFrame(opcode byte, payload []byte, mask [4]byte) []byte {
	frame := []byte{0x80 | opcode, 0x80 | byte(len(payload)), mask[0], mask[1], mask[2], mask[3]}
	for index, value := range payload {
		frame = append(frame, value^mask[index%4])
	}
	return frame
}
