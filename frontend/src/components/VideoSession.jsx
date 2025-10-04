import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const VideoSession = ({ sessionId, participantId, mode = 'group' }) => {
  const [localStream, setLocalStream] = useState(null);
  const [remoteStreams, setRemoteStreams] = useState([]);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isAudioOn, setIsAudioOn] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [sessionNotes, setSessionNotes] = useState('');
  const [testObservation, setTestObservation] = useState({
    type: 'saliva',
    substances: ['methamphetamine', 'cocaine'],
    results: {},
    notes: ''
  });

  const localVideoRef = useRef(null);
  const remoteVideoRefs = useRef([]);
  const mediaRecorderRef = useRef(null);
  const recordedChunks = useRef([]);

  useEffect(() => {
    initializeMedia();
    return () => {
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const initializeMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
        audio: true
      });
      setLocalStream(stream);
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error('Error accessing media devices:', error);
      alert('Please grant camera and microphone permissions');
    }
  };

  const toggleVideo = () => {
    if (localStream) {
      localStream.getVideoTracks().forEach(track => {
        track.enabled = !track.enabled;
      });
      setIsVideoOn(!isVideoOn);
    }
  };

  const toggleAudio = () => {
    if (localStream) {
      localStream.getAudioTracks().forEach(track => {
        track.enabled = !track.enabled;
      });
      setIsAudioOn(!isAudioOn);
    }
  };

  const startRecording = () => {
    if (!localStream) return;

    recordedChunks.current = [];
    const options = { mimeType: 'video/webm;codecs=vp9' };
    mediaRecorderRef.current = new MediaRecorder(localStream, options);

    mediaRecorderRef.current.ondataavailable = (event) => {
      if (event.data.size > 0) {
        recordedChunks.current.push(event.data);
      }
    };

    mediaRecorderRef.current.onstop = () => {
      const blob = new Blob(recordedChunks.current, { type: 'video/webm' });
      // In production, upload this blob to cloud storage
      const url = URL.createObjectURL(blob);
      console.log('Recording saved:', url);
    };

    mediaRecorderRef.current.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const captureSnapshot = async () => {
    if (!localVideoRef.current) return;

    const canvas = document.createElement('canvas');
    canvas.width = localVideoRef.current.videoWidth;
    canvas.height = localVideoRef.current.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(localVideoRef.current, 0, 0);

    // Convert to blob and upload
    canvas.toBlob(async (blob) => {
      // In production, upload to cloud storage
      const formData = new FormData();
      formData.append('image', blob, `test_${Date.now()}.png`);
      console.log('Snapshot captured');
    });
  };

  const submitTestResult = async () => {
    try {
      const response = await axios.post(
        'http://localhost:5001/api/cpss/drug-tests',
        {
          participant_id: participantId,
          session_id: sessionId,
          test_type: testObservation.type,
          observation_method: 'video',
          substances_tested: testObservation.substances,
          results: testObservation.results,
          notes: testObservation.notes,
          video_url: isRecording ? 'recording_url_here' : null
        },
        { withCredentials: true }
      );

      if (response.data.success) {
        alert('Test result recorded successfully');
        // Reset form
        setTestObservation({
          type: 'saliva',
          substances: ['methamphetamine', 'cocaine'],
          results: {},
          notes: ''
        });
      }
    } catch (error) {
      console.error('Error submitting test result:', error);
      alert('Failed to submit test result');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">
            {mode === 'group' ? 'Group Session' : 'Drug Test Observation'}
          </h1>
          <button
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg"
            onClick={() => window.close()}
          >
            End Session
          </button>
        </div>

        {/* Video Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          {/* Local Video */}
          <div className="relative bg-gray-800 rounded-lg overflow-hidden">
            <video
              ref={localVideoRef}
              autoPlay
              muted
              playsInline
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-4 left-4 text-sm bg-black bg-opacity-50 px-2 py-1 rounded">
              You (CPSS)
            </div>
          </div>

          {/* Remote Videos */}
          {mode === 'group' ? (
            <div className="grid grid-cols-2 gap-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-gray-800 rounded-lg aspect-video flex items-center justify-center">
                  <p className="text-gray-500">Participant {i}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-gray-800 rounded-lg aspect-video flex items-center justify-center">
              <p className="text-gray-500">Participant Video</p>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <div className="flex justify-center space-x-4">
            <button
              onClick={toggleVideo}
              className={`px-4 py-2 rounded-lg ${
                isVideoOn ? 'bg-blue-600 hover:bg-blue-700' : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              {isVideoOn ? '📹 Video On' : '📹 Video Off'}
            </button>

            <button
              onClick={toggleAudio}
              className={`px-4 py-2 rounded-lg ${
                isAudioOn ? 'bg-blue-600 hover:bg-blue-700' : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              {isAudioOn ? '🎤 Audio On' : '🎤 Audio Off'}
            </button>

            {mode === 'test' && (
              <>
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`px-4 py-2 rounded-lg ${
                    isRecording ? 'bg-red-600 hover:bg-red-700 animate-pulse' : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {isRecording ? '⏹ Stop Recording' : '⏺ Start Recording'}
                </button>

                <button
                  onClick={captureSnapshot}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg"
                >
                  📸 Capture Photo
                </button>
              </>
            )}
          </div>
        </div>

        {/* Side Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Session Notes */}
          <div className="lg:col-span-2 bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Session Notes</h2>
            <textarea
              value={sessionNotes}
              onChange={(e) => setSessionNotes(e.target.value)}
              className="w-full h-32 p-3 bg-gray-700 rounded-lg resize-none"
              placeholder="Enter session observations..."
            />
          </div>

          {/* Drug Test Observation Form (if in test mode) */}
          {mode === 'test' && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Test Observation</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm mb-2">Test Type</label>
                  <select
                    value={testObservation.type}
                    onChange={(e) => setTestObservation({ ...testObservation, type: e.target.value })}
                    className="w-full p-2 bg-gray-700 rounded"
                  >
                    <option value="saliva">Saliva</option>
                    <option value="urine">Urine</option>
                    <option value="breathalyzer">Breathalyzer</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm mb-2">Substances Tested</label>
                  {testObservation.substances.map((substance) => (
                    <div key={substance} className="flex items-center justify-between mb-2">
                      <span className="text-sm">{substance}</span>
                      <select
                        onChange={(e) => {
                          setTestObservation({
                            ...testObservation,
                            results: {
                              ...testObservation.results,
                              [substance]: e.target.value
                            }
                          });
                        }}
                        className="p-1 bg-gray-700 rounded text-sm"
                      >
                        <option value="">Select</option>
                        <option value="negative">Negative</option>
                        <option value="positive">Positive</option>
                        <option value="invalid">Invalid</option>
                      </select>
                    </div>
                  ))}
                </div>

                <div>
                  <label className="block text-sm mb-2">Notes</label>
                  <textarea
                    value={testObservation.notes}
                    onChange={(e) => setTestObservation({ ...testObservation, notes: e.target.value })}
                    className="w-full h-20 p-2 bg-gray-700 rounded resize-none text-sm"
                    placeholder="Additional observations..."
                  />
                </div>

                <button
                  onClick={submitTestResult}
                  className="w-full py-2 bg-green-600 hover:bg-green-700 rounded-lg"
                >
                  Submit Test Result
                </button>
              </div>
            </div>
          )}

          {/* Participants List (if in group mode) */}
          {mode === 'group' && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Participants</h2>
              <div className="space-y-2">
                {['John D.', 'Sarah M.', 'Mike R.', 'Lisa K.'].map((name) => (
                  <div key={name} className="flex items-center justify-between p-2 bg-gray-700 rounded">
                    <span>{name}</span>
                    <div className="flex space-x-2">
                      <span className="text-green-400">●</span>
                      <button className="text-xs text-blue-400">Observe Test</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoSession;