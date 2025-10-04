import React, { useState, useEffect } from 'react';
import axios from 'axios';

const CPSSDashboard = () => {
  const [activeView, setActiveView] = useState('overview');
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedPod, setSelectedPod] = useState(null);
  const [selectedParticipant, setSelectedParticipant] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:5001/api/cpss/dashboard', {
        withCredentials: true
      });
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPodParticipants = async (podId) => {
    try {
      const response = await axios.get(
        `http://localhost:5001/api/cpss/pods/${podId}/participants`,
        { withCredentials: true }
      );
      return response.data.participants;
    } catch (error) {
      console.error('Error fetching participants:', error);
      return [];
    }
  };

  const startGroupSession = async (sessionId) => {
    try {
      const response = await axios.post(
        `http://localhost:5001/api/cpss/sessions/${sessionId}/start`,
        {},
        { withCredentials: true }
      );

      if (response.data.video_url) {
        window.open(response.data.video_url, '_blank');
      }
    } catch (error) {
      console.error('Error starting session:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">CPSS Dashboard</h1>
        <p className="text-gray-600">Manage your contingency management pods</p>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg shadow-sm mb-6">
        <div className="flex border-b">
          {['overview', 'pods', 'sessions', 'tests', 'billing'].map((view) => (
            <button
              key={view}
              onClick={() => setActiveView(view)}
              className={`px-6 py-3 font-medium capitalize transition-colors ${
                activeView === view
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              {view}
            </button>
          ))}
        </div>
      </div>

      {/* Content Area */}
      {activeView === 'overview' && dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Stats Cards */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Active Participants</h3>
            <p className="text-3xl font-bold text-gray-900">
              {dashboardData.stats?.total_active_participants || 0}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Sessions Today</h3>
            <p className="text-3xl font-bold text-gray-900">
              {dashboardData.stats?.sessions_today || 0}
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Pending Reviews</h3>
            <p className="text-3xl font-bold text-gray-900">
              {dashboardData.stats?.pending_reviews || 0}
            </p>
          </div>

          {/* Today's Sessions */}
          <div className="col-span-full bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4">Today's Sessions</h2>
            {dashboardData.today_sessions?.length > 0 ? (
              <div className="space-y-3">
                {dashboardData.today_sessions.map((session) => (
                  <div
                    key={session.id}
                    className="flex justify-between items-center p-4 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <p className="font-medium">{session.pod_name}</p>
                      <p className="text-sm text-gray-600">
                        {new Date(session.scheduled_time).toLocaleTimeString()} - {session.session_type}
                      </p>
                    </div>
                    {session.status === 'scheduled' && (
                      <button
                        onClick={() => startGroupSession(session.id)}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                      >
                        Start Session
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No sessions scheduled for today</p>
            )}
          </div>

          {/* Upcoming Milestones */}
          <div className="col-span-full bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold mb-4">Upcoming Milestones</h2>
            {dashboardData.upcoming_milestones?.length > 0 ? (
              <div className="space-y-3">
                {dashboardData.upcoming_milestones.map((milestone) => (
                  <div
                    key={milestone.id}
                    className="p-4 bg-green-50 border border-green-200 rounded-lg"
                  >
                    <p className="font-medium">
                      {milestone.patient_first_name} {milestone.patient_last_name}
                    </p>
                    <p className="text-sm text-green-700">{milestone.milestone_status}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No upcoming milestones</p>
            )}
          </div>
        </div>
      )}

      {/* Pods View */}
      {activeView === 'pods' && dashboardData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">My Pods</h2>
              <div className="space-y-3">
                {dashboardData.pods?.map((pod) => (
                  <button
                    key={pod.id}
                    onClick={() => setSelectedPod(pod)}
                    className={`w-full text-left p-4 rounded-lg transition-colors ${
                      selectedPod?.id === pod.id
                        ? 'bg-blue-50 border border-blue-300'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <p className="font-medium">{pod.name}</p>
                    <p className="text-sm text-gray-600">
                      {pod.participant_count}/{pod.max_participants} participants
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            {selectedPod ? (
              <PodDetails
                pod={selectedPod}
                onSelectParticipant={setSelectedParticipant}
                fetchParticipants={fetchPodParticipants}
              />
            ) : (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <p className="text-gray-500">Select a pod to view details</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Pod Details Component
const PodDetails = ({ pod, onSelectParticipant, fetchParticipants }) => {
  const [participants, setParticipants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadParticipants();
  }, [pod.id]);

  const loadParticipants = async () => {
    setLoading(true);
    const data = await fetchParticipants(pod.id);
    setParticipants(data);
    setLoading(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h2 className="text-xl font-semibold mb-4">{pod.name} - Participants</h2>

      {loading ? (
        <p>Loading participants...</p>
      ) : (
        <div className="space-y-4">
          {participants.map((participant) => (
            <div
              key={participant.id}
              className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
              onClick={() => onSelectParticipant(participant)}
            >
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-medium">
                    {participant.patient_first_name} {participant.patient_last_name}
                  </p>
                  <p className="text-sm text-gray-600">
                    Phase: {participant.progress_phase} | Attendance: {participant.attendance_rate?.toFixed(0)}%
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">
                    Joined: {new Date(participant.joined_date).toLocaleDateString()}
                  </p>
                  {participant.last_test_date && (
                    <p className="text-sm text-gray-500">
                      Last test: {new Date(participant.last_test_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mt-3">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>Progress</span>
                  <span>{participant.total_sessions_attended || 0} sessions</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{
                      width: `${Math.min(
                        (participant.total_sessions_attended || 0) / 12 * 100,
                        100
                      )}%`
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CPSSDashboard;