export default function ResultScreen({ result, onCheckAnother, onContinueEnrollment }) {
  const isQualified = result.success && result.qualified;
  const details = result.eligibility_details || {};

  // Helper to format the enrollment status message
  const getStatusMessage = () => {
    if (!result.success) return "Unable to verify eligibility";

    if (isQualified) {
      return "Enrolled in Traditional Medicaid FFS";
    }

    // Check for specific managed care organizations
    const eligInfo = details.eligibility_info || [];
    const planDetails = details.plan_details || {};

    // Look for MCO information
    for (const info of eligInfo) {
      if (info.plan_name && info.plan_name.toLowerCase().includes('molina')) {
        return "Enrolled in Molina Healthcare (Managed Care)";
      }
      if (info.plan_name && info.plan_name.toLowerCase().includes('selecthealth')) {
        return "Enrolled in SelectHealth (Managed Care)";
      }
      if (info.plan_name && info.plan_name.toLowerCase().includes('anthem')) {
        return "Enrolled in Anthem (Managed Care)";
      }
      if (info.plan_name && info.plan_name.toLowerCase().includes('healthy u')) {
        return "Enrolled in Healthy U (Managed Care)";
      }
    }

    // Check FFS status
    if (details.ffs_status === 'NOT_ENROLLED') {
      return "Not currently enrolled in Utah Medicaid";
    }

    if (details.ffs_status === 'MANAGED_CARE') {
      return "Enrolled in Managed Care (not FFS)";
    }

    return details.enrollment_type || "Enrollment status unclear";
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className={`p-8 rounded-lg text-center mb-6 ${
        isQualified ? 'bg-green-50 border-2 border-green-500' : 'bg-yellow-50 border-2 border-yellow-500'
      }`}>
        {isQualified ? (
          <>
            <div className="text-6xl mb-4">✅</div>
            <h2 className="text-2xl font-bold text-green-800 mb-2">
              This patient qualifies for CM enrollment
            </h2>
            <p className="text-lg text-green-700">{getStatusMessage()}</p>
            {result.patient_info && (
              <div className="mt-4 text-left bg-white p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1"><strong>Name:</strong> {result.patient_info.first_name} {result.patient_info.last_name}</p>
                {result.patient_info.medicaid_id && (
                  <p className="text-sm text-gray-600"><strong>Medicaid ID:</strong> {result.patient_info.medicaid_id}</p>
                )}
              </div>
            )}
          </>
        ) : (
          <>
            <div className="text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-yellow-800 mb-2">
              Cannot enroll at this time
            </h2>
            <p className="text-lg text-yellow-700 mt-2">{getStatusMessage()}</p>
            {result.error && (
              <p className="text-sm text-gray-600 mt-2">{result.error}</p>
            )}
          </>
        )}
      </div>

      {/* Debug Information Panel */}
      <div className="mt-6 p-4 bg-gray-100 rounded-lg">
        <details className="cursor-pointer">
          <summary className="font-bold text-gray-700">Debug: UHIN Response Data (Click to expand)</summary>
          <div className="mt-4 space-y-3 text-left text-sm">
            <div className="bg-white p-3 rounded">
              <h3 className="font-semibold mb-2">Basic Status:</h3>
              <p><strong>FFS Status:</strong> {details.ffs_status}</p>
              <p><strong>FFS Qualification:</strong> {details.ffs_qualification}</p>
              <p><strong>Is Enrolled:</strong> {details.is_enrolled ? 'Yes' : 'No'}</p>
              <p><strong>Enrollment Type:</strong> {details.enrollment_type}</p>
            </div>

            {details.patient_info && Object.keys(details.patient_info).length > 0 && (
              <div className="bg-white p-3 rounded">
                <h3 className="font-semibold mb-2">Patient Information from UHIN:</h3>
                <pre className="text-xs overflow-x-auto">{JSON.stringify(details.patient_info, null, 2)}</pre>
              </div>
            )}

            {details.payer_info && Object.keys(details.payer_info).length > 0 && (
              <div className="bg-white p-3 rounded">
                <h3 className="font-semibold mb-2">Payer Information:</h3>
                <pre className="text-xs overflow-x-auto">{JSON.stringify(details.payer_info, null, 2)}</pre>
              </div>
            )}

            {details.eligibility_info && details.eligibility_info.length > 0 && (
              <div className="bg-white p-3 rounded">
                <h3 className="font-semibold mb-2">Eligibility Details:</h3>
                <pre className="text-xs overflow-x-auto">{JSON.stringify(details.eligibility_info, null, 2)}</pre>
              </div>
            )}

            {details.plan_details && Object.keys(details.plan_details).length > 0 && (
              <div className="bg-white p-3 rounded">
                <h3 className="font-semibold mb-2">Plan Details:</h3>
                <pre className="text-xs overflow-x-auto">{JSON.stringify(details.plan_details, null, 2)}</pre>
              </div>
            )}

            {details.rejection_reasons && details.rejection_reasons.length > 0 && (
              <div className="bg-white p-3 rounded">
                <h3 className="font-semibold mb-2">Rejection Reasons:</h3>
                <ul className="list-disc list-inside">
                  {details.rejection_reasons.map((reason, idx) => (
                    <li key={idx}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}

            {details.raw_response_summary && Object.keys(details.raw_response_summary).length > 0 && (
              <div className="bg-white p-3 rounded">
                <h3 className="font-semibold mb-2">Raw Response Summary:</h3>
                <pre className="text-xs overflow-x-auto">{JSON.stringify(details.raw_response_summary, null, 2)}</pre>
              </div>
            )}
          </div>
        </details>
      </div>

      <div className="space-y-3 mt-6">
        {isQualified && (
          <button
            onClick={onContinueEnrollment}
            className="w-full bg-green-600 text-white p-4 rounded-lg text-lg font-semibold hover:bg-green-700 transition-colors"
          >
            Continue Enrollment
          </button>
        )}

        <button
          onClick={onCheckAnother}
          className="w-full bg-blue-600 text-white p-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
        >
          Check Another Patient
        </button>
      </div>
    </div>
  );
}
