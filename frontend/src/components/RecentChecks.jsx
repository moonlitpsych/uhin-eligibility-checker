import { useEffect, useState } from 'react';
import axios from 'axios';

export default function RecentChecks({ onSelectCheck }) {
  const [checks, setChecks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecentChecks();
  }, []);

  const fetchRecentChecks = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/eligibility/recent');
      setChecks(response.data.checks || []);
    } catch (error) {
      console.error('Failed to fetch recent checks:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center text-gray-500 mt-4">Loading recent checks...</div>;
  }

  if (checks.length === 0) {
    return null;
  }

  return (
    <div className="max-w-md mx-auto p-6 mt-8">
      <h2 className="text-xl font-bold mb-4">Recent Checks</h2>
      <div className="space-y-2">
        {checks.map((check, index) => (
          <div
            key={index}
            onClick={() => onSelectCheck && onSelectCheck(check)}
            className="p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
          >
            <div className="flex justify-between items-center">
              <div>
                <p className="font-semibold">{check.first_name} {check.last_name}</p>
                <p className="text-sm text-gray-600">DOB: {check.date_of_birth}</p>
              </div>
              <div className={`px-3 py-1 rounded-full text-sm font-semibold ${
                check.qualified ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
              }`}>
                {check.qualified ? 'Qualified' : 'Not Qualified'}
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">{new Date(check.checked_at).toLocaleString()}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
