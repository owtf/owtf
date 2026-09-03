package proxy

import (
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"strings"
	"sync"
	"time"
)

const maximumWebSocketFrames = 10_000

type webSocketCapture struct {
	mu             sync.Mutex
	maximum        int
	payloadMaximum int
	frameMaximum   int
	payloadBytes   int
	nextSequence   uint64
	droppedFrames  int
	frames         []webSocketFrame
}

type webSocketFrame struct {
	Sequence      uint64    `json:"sequence"`
	Direction     string    `json:"direction"`
	CapturedAt    time.Time `json:"captured_at"`
	Final         bool      `json:"final"`
	RSV1          bool      `json:"rsv1"`
	RSV2          bool      `json:"rsv2"`
	RSV3          bool      `json:"rsv3"`
	Opcode        uint8     `json:"opcode"`
	Masked        bool      `json:"masked"`
	PayloadLength uint64    `json:"payload_length"`
	PayloadBase64 string    `json:"payload_base64"`
	Truncated     bool      `json:"truncated"`
	ProtocolError string    `json:"protocol_error,omitempty"`
	payload       []byte
}

type webSocketTranscript struct {
	Version       string           `json:"version"`
	Frames        []webSocketFrame `json:"frames"`
	DroppedFrames int              `json:"dropped_frames"`
	Truncated     bool             `json:"truncated"`
}

type webSocketStream struct {
	capture      *webSocketCapture
	direction    string
	expectsMask  bool
	header       [14]byte
	headerLength int
	headerNeed   int
	frame        webSocketFrame
	payloadRead  uint64
	closed       bool
	stopped      bool
}

func newWebSocketCapture(maximumBody int64) *webSocketCapture {
	maximum := int(maximumBody)
	if maximumBody > int64(maxInt()) {
		maximum = maxInt()
	}
	frames := maximum / 1024
	if frames < 1 {
		frames = 1
	}
	if frames > maximumWebSocketFrames {
		frames = maximumWebSocketFrames
	}
	return &webSocketCapture{
		maximum: maximum, payloadMaximum: maximum / 2, frameMaximum: frames,
		frames: make([]webSocketFrame, 0, frames),
	}
}

func (capture *webSocketCapture) stream(direction string, expectsMask bool) *webSocketStream {
	return &webSocketStream{
		capture: capture, direction: direction, expectsMask: expectsMask, headerNeed: 2,
	}
}

func (capture *webSocketCapture) payloadLimit() int {
	capture.mu.Lock()
	defer capture.mu.Unlock()
	remaining := capture.payloadMaximum - capture.payloadBytes
	if remaining < 0 {
		return 0
	}
	return remaining
}

func (capture *webSocketCapture) add(frame webSocketFrame) bool {
	capture.mu.Lock()
	defer capture.mu.Unlock()
	if len(capture.frames) >= capture.frameMaximum {
		capture.droppedFrames++
		return false
	}
	remaining := capture.payloadMaximum - capture.payloadBytes
	if remaining < len(frame.payload) {
		if remaining < 0 {
			remaining = 0
		}
		frame.payload = frame.payload[:remaining]
		frame.Truncated = true
	}
	frame.Truncated = frame.Truncated || uint64(len(frame.payload)) < frame.PayloadLength
	payloadBytes := len(frame.payload)
	frame.PayloadBase64 = base64.StdEncoding.EncodeToString(frame.payload)
	frame.payload = nil
	capture.payloadBytes += payloadBytes
	capture.nextSequence++
	frame.Sequence = capture.nextSequence
	frame.CapturedAt = time.Now().UTC()
	capture.frames = append(capture.frames, frame)
	return true
}

func (capture *webSocketCapture) bytes() []byte {
	capture.mu.Lock()
	frames := append([]webSocketFrame(nil), capture.frames...)
	dropped := capture.droppedFrames
	maximum := capture.maximum
	capture.mu.Unlock()
	if len(frames) == 0 {
		return nil
	}
	transcript := webSocketTranscript{Version: "1", Frames: frames, DroppedFrames: dropped, Truncated: dropped > 0}
	for {
		data, err := json.Marshal(transcript)
		if err != nil {
			return nil
		}
		if len(data) <= maximum {
			return data
		}
		if len(transcript.Frames) == 0 {
			return nil
		}
		last := len(transcript.Frames) - 1
		transcript.Frames = transcript.Frames[:last]
		transcript.DroppedFrames++
		transcript.Truncated = true
	}
}

func (stream *webSocketStream) Write(data []byte) (int, error) {
	written := len(data)
	for len(data) > 0 && !stream.stopped {
		if stream.headerLength < stream.headerNeed {
			count := copy(stream.header[stream.headerLength:stream.headerNeed], data)
			stream.headerLength += count
			data = data[count:]
			if stream.headerLength < stream.headerNeed {
				continue
			}
		}
		if stream.headerNeed == 2 {
			stream.headerNeed = frameHeaderLength(stream.header[1])
			if stream.headerLength < stream.headerNeed {
				continue
			}
		}
		if stream.frame.PayloadLength == 0 && stream.payloadRead == 0 {
			if !stream.startFrame() {
				continue
			}
			if stream.frame.PayloadLength == 0 {
				stream.finishFrame()
				continue
			}
		}
		remaining := stream.frame.PayloadLength - stream.payloadRead
		count := uint64(len(data))
		if count > remaining {
			count = remaining
		}
		stream.capturePayload(data[:count])
		stream.payloadRead += count
		data = data[count:]
		if stream.payloadRead == stream.frame.PayloadLength {
			stream.finishFrame()
		}
	}
	return written, nil
}

func (stream *webSocketStream) Close() {
	if stream.closed || stream.stopped {
		return
	}
	stream.closed = true
	if stream.headerLength == 0 && stream.frame.PayloadLength == 0 {
		return
	}
	if stream.frame.Direction == "" {
		stream.frame.Direction = stream.direction
		stream.frame.ProtocolError = "incomplete frame header"
	} else {
		stream.frame.ProtocolError = joinProtocolError(stream.frame.ProtocolError, "incomplete frame payload")
		stream.frame.Truncated = true
	}
	stream.capture.add(stream.frame)
}

func (stream *webSocketStream) startFrame() bool {
	first := stream.header[0]
	second := stream.header[1]
	masked := second&0x80 != 0
	lengthCode := second & 0x7f
	offset := 2
	var length uint64
	switch lengthCode {
	case 126:
		length = uint64(binary.BigEndian.Uint16(stream.header[offset : offset+2]))
		offset += 2
	case 127:
		length = binary.BigEndian.Uint64(stream.header[offset : offset+8])
		offset += 8
	default:
		length = uint64(lengthCode)
	}
	stream.frame = webSocketFrame{
		Direction: stream.direction, Final: first&0x80 != 0,
		RSV1: first&0x40 != 0, RSV2: first&0x20 != 0, RSV3: first&0x10 != 0,
		Opcode: first & 0x0f, Masked: masked, PayloadLength: length,
	}
	if lengthCode == 127 && length&(uint64(1)<<63) != 0 {
		stream.frame.ProtocolError = "invalid 64-bit payload length"
		stream.capture.add(stream.frame)
		stream.stopped = true
		return false
	}
	if masked != stream.expectsMask {
		stream.frame.ProtocolError = "unexpected masking"
	}
	if !validWebSocketOpcode(stream.frame.Opcode) {
		stream.frame.ProtocolError = joinProtocolError(stream.frame.ProtocolError, "reserved opcode")
	}
	if stream.frame.Opcode >= 8 && (!stream.frame.Final || length > 125) {
		stream.frame.ProtocolError = joinProtocolError(stream.frame.ProtocolError, "invalid control frame")
	}
	if masked {
		copy(stream.header[10:14], stream.header[offset:offset+4])
	}
	limit := stream.capture.payloadLimit()
	if uint64(limit) > length {
		limit = int(length)
	}
	stream.frame.payload = make([]byte, 0, limit)
	return true
}

func (stream *webSocketStream) capturePayload(data []byte) {
	remaining := cap(stream.frame.payload) - len(stream.frame.payload)
	if remaining <= 0 {
		return
	}
	if len(data) > remaining {
		data = data[:remaining]
	}
	start := stream.payloadRead
	for index, value := range data {
		if stream.frame.Masked {
			value ^= stream.header[10+int((start+uint64(index))%4)]
		}
		stream.frame.payload = append(stream.frame.payload, value)
	}
}

func (stream *webSocketStream) finishFrame() {
	if !stream.capture.add(stream.frame) {
		stream.stopped = true
	}
	stream.frame = webSocketFrame{}
	stream.payloadRead = 0
	stream.headerLength = 0
	stream.headerNeed = 2
}

func frameHeaderLength(second byte) int {
	length := 2
	switch second & 0x7f {
	case 126:
		length += 2
	case 127:
		length += 8
	}
	if second&0x80 != 0 {
		length += 4
	}
	return length
}

func validWebSocketOpcode(opcode uint8) bool {
	return opcode <= 2 || opcode == 8 || opcode == 9 || opcode == 10
}

func joinProtocolError(current, next string) string {
	if current == "" {
		return next
	}
	return strings.Join([]string{current, next}, "; ")
}

func maxInt() int {
	return int(^uint(0) >> 1)
}
