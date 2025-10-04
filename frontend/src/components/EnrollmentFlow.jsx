import { useState } from 'react';
import { ChevronRight, CheckCircle, AlertCircle, Phone, MapPin, Calendar, User } from 'lucide-react';

const EnrollmentFlow = ({ patientData, onComplete, onCancel }) => {
  const [currentStep, setCurrentStep] = useState(1);

  // Extract all available data from eligibility check
  const patientInfo = patientData?.eligibility_details?.patient_info || patientData?.patient_info || {};
  const payerInfo = patientData?.eligibility_details?.payer_info || {};

  const [enrollmentData, setEnrollmentData] = useState({
    // Pre-filled from eligibility check - use all available data
    firstName: patientInfo.first_name || patientInfo.firstName || '',
    lastName: patientInfo.last_name || patientInfo.lastName || '',
    medicaidId: patientInfo.member_id || patientInfo.medicaid_id || '',
    dob: patientInfo.dob || patientData?.date_of_birth || '',

    // New fields to collect
    phone: '',
    altPhone: '',
    email: '',
    preferredContact: 'text', // Default to text for URL sharing

    // Address
    street: '',
    apt: '',
    city: '',
    state: 'UT',
    zip: '',

    // Program specific
    primaryDiagnosis: '',
    substanceUseHistory: '',
    enrollmentLocation: '',
    referralSource: 'CPSS_Zack_USARA', // Auto-captured from logged-in user

    // Consent
    consentGiven: false,
    consentDate: new Date().toISOString().split('T')[0],
    consentMethod: 'in_person',
    witnessName: '',

    // Emergency Contact
    emergencyName: '',
    emergencyRelation: '',
    emergencyPhone: ''
  });

  const updateField = (field, value) => {
    setEnrollmentData(prev => ({ ...prev, [field]: value }));
  };

  const steps = [
    { number: 1, title: 'Contact Info', icon: Phone },
    { number: 2, title: 'Address', icon: MapPin },
    { number: 3, title: 'Program Info', icon: User },
    { number: 4, title: 'Consent', icon: CheckCircle },
    { number: 5, title: 'Review', icon: Calendar }
  ];

  const handleNext = () => {
    if (currentStep < 5) {
      setCurrentStep(currentStep + 1);
    } else {
      // Submit enrollment
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5001/api/enrollment/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...enrollmentData,
          eligibilityData: patientData,
          enrolledBy: 'CPSS_User', // Would come from auth
          enrollmentDate: new Date().toISOString()
        })
      });

      if (response.ok) {
        const result = await response.json();
        onComplete(result);
      } else {
        console.error('Enrollment failed');
      }
    } catch (error) {
      console.error('Error submitting enrollment:', error);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return <ContactInfoStep data={enrollmentData} updateField={updateField} />;
      case 2:
        return <AddressStep data={enrollmentData} updateField={updateField} />;
      case 3:
        return <ProgramInfoStep data={enrollmentData} updateField={updateField} />;
      case 4:
        return <ConsentStep data={enrollmentData} updateField={updateField} />;
      case 5:
        return <ReviewStep data={enrollmentData} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Progress Bar */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon;
              const isActive = step.number === currentStep;
              const isCompleted = step.number < currentStep;

              return (
                <div key={step.number} className="flex items-center">
                  <div className={`flex items-center ${index < steps.length - 1 ? 'flex-1' : ''}`}>
                    <div className={`
                      rounded-full p-2 transition-colors
                      ${isActive ? 'bg-blue-600 text-white' : ''}
                      ${isCompleted ? 'bg-green-600 text-white' : ''}
                      ${!isActive && !isCompleted ? 'bg-gray-200 text-gray-400' : ''}
                    `}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className={`ml-2 text-sm font-medium
                      ${isActive || isCompleted ? 'text-gray-900' : 'text-gray-400'}
                    `}>
                      {step.title}
                    </span>
                  </div>
                  {index < steps.length - 1 && (
                    <ChevronRight className="w-5 h-5 mx-2 text-gray-300" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          {/* Patient Header */}
          <div className="mb-6 pb-4 border-b">
            <h2 className="text-xl font-semibold text-gray-900">
              Enrolling: {enrollmentData.firstName} {enrollmentData.lastName}
            </h2>
            <p className="text-sm text-gray-600">
              Medicaid ID: {enrollmentData.medicaidId} | TAM Eligible
            </p>
          </div>

          {/* Step Content */}
          <div className="mb-8">
            {renderStepContent()}
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between">
            <button
              onClick={currentStep === 1 ? onCancel : handleBack}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              {currentStep === 1 ? 'Cancel' : 'Back'}
            </button>

            <button
              onClick={handleNext}
              className={`px-6 py-2 rounded-md text-white font-medium
                ${currentStep === 5 ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'}
              `}
            >
              {currentStep === 5 ? 'Complete Enrollment' : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Step 1: Contact Information
const ContactInfoStep = ({ data, updateField }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-medium text-gray-900 mb-4">Contact Information</h3>

    <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
      <div className="flex items-start">
        <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
        <div className="text-sm text-blue-800">
          <p className="font-medium">Quick Enrollment Tip</p>
          <p>Only the primary phone is required. Additional contact info can be collected during the patient's first session.</p>
        </div>
      </div>
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Primary Phone Number *
      </label>
      <input
        type="tel"
        value={data.phone}
        onChange={(e) => updateField('phone', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        placeholder="(555) 123-4567"
        required
        autoFocus
      />
      <p className="text-xs text-gray-500 mt-1">We'll use this to schedule the first peer support session</p>
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Alternative Phone (Optional)
      </label>
      <input
        type="tel"
        value={data.altPhone}
        onChange={(e) => updateField('altPhone', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        placeholder="(555) 123-4567"
      />
    </div>

    <div className="bg-green-50 border border-green-200 rounded-md p-4">
      <div className="flex items-start">
        <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 mr-2 flex-shrink-0" />
        <div className="text-sm text-green-800">
          <p className="font-medium mb-1">Text Message Outreach</p>
          <p>We'll send the patient a text message with a link to download the CM app and complete their onboarding.</p>
          <p className="text-xs mt-1 italic">Future integration with Notifyre will automate this process.</p>
        </div>
      </div>
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Email Address (Optional)
      </label>
      <input
        type="email"
        value={data.email}
        onChange={(e) => updateField('email', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        placeholder="patient@example.com"
      />
      <p className="text-xs text-gray-500 mt-1">For sending program information and reminders</p>
    </div>

    {/* Removed emergency contact section - can be collected during first session */}
  </div>
);

// Step 2: Address
const AddressStep = ({ data, updateField }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-medium text-gray-900 mb-4">Current Address</h3>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Street Address *
      </label>
      <input
        type="text"
        value={data.street}
        onChange={(e) => updateField('street', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        required
      />
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Apartment/Unit
      </label>
      <input
        type="text"
        value={data.apt}
        onChange={(e) => updateField('apt', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
      />
    </div>

    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      <div className="col-span-1">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          City *
        </label>
        <input
          type="text"
          value={data.city}
          onChange={(e) => updateField('city', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          State *
        </label>
        <select
          value={data.state}
          onChange={(e) => updateField('state', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="UT">Utah</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          ZIP Code *
        </label>
        <input
          type="text"
          value={data.zip}
          onChange={(e) => updateField('zip', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          pattern="[0-9]{5}"
          maxLength="5"
          required
        />
      </div>
    </div>

    <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mt-4">
      <div className="flex items-start">
        <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0" />
        <div className="text-sm text-blue-800">
          <p className="font-medium mb-1">Housing Status Note</p>
          <p>If the patient is experiencing homelessness or housing instability, please note this in the referral source field and connect them with appropriate resources.</p>
        </div>
      </div>
    </div>
  </div>
);

// Step 3: Program Information
const ProgramInfoStep = ({ data, updateField }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-medium text-gray-900 mb-4">Program Information</h3>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Stimulant Use Disorder Status *
      </label>
      <select
        value={data.primaryDiagnosis}
        onChange={(e) => updateField('primaryDiagnosis', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        required
      >
        <option value="">Select status</option>
        <option value="meth_active">Methamphetamine - Active Use</option>
        <option value="meth_early_recovery">Methamphetamine - Early Recovery (0-3 months)</option>
        <option value="cocaine_active">Cocaine/Crack - Active Use</option>
        <option value="cocaine_early_recovery">Cocaine/Crack - Early Recovery (0-3 months)</option>
        <option value="polysubstance_stimulant">Polysubstance with Primary Stimulant</option>
        <option value="other_stimulant">Other Stimulant (Adderall, etc.)</option>
      </select>
      <p className="text-xs text-gray-500 mt-1">CM for stimulant use disorder is evidence-based and covered by Medicaid</p>
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Additional Clinical Notes
      </label>
      <textarea
        value={data.substanceUseHistory}
        onChange={(e) => updateField('substanceUseHistory', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        rows="3"
        placeholder="Treatment history, co-occurring conditions, motivation level, etc."
      />
    </div>

    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Enrollment Location *
      </label>
      <select
        value={data.enrollmentLocation}
        onChange={(e) => updateField('enrollmentLocation', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        required
      >
        <option value="">Select location</option>
        <option value="uofu_hospital_ed">University Hospital - Emergency Dept</option>
        <option value="uofu_hospital_inpatient">University Hospital - Inpatient</option>
        <option value="huntsman_mental_health">Huntsman Mental Health Institute</option>
        <option value="lds_hospital">LDS Hospital</option>
        <option value="salt_lake_regional">Salt Lake Regional Medical Center</option>
        <option value="st_marks">St. Mark's Hospital</option>
        <option value="imh_hospital">Intermountain Medical Center</option>
        <option value="other_slc_hospital">Other Salt Lake County Hospital</option>
      </select>
    </div>

    {/* Referral source auto-captured from logged-in CPSS */}
    <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
      <div className="text-sm text-gray-600">
        <p className="font-medium">Referral Source</p>
        <p>CPSS: Zack (USARA Peer Support Specialist)</p>
        <p className="text-xs mt-1">Auto-captured from logged-in user</p>
      </div>
    </div>

    <div className="bg-green-50 border border-green-200 rounded-md p-4 mt-4">
      <div className="flex items-start">
        <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 mr-2 flex-shrink-0" />
        <div className="text-sm text-green-800">
          <p className="font-medium mb-1">Program Benefits</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Weekly peer support sessions (H0038 billable)</li>
            <li>Incentive rewards for meeting goals</li>
            <li>Connection to community resources</li>
            <li>24/7 crisis support line access</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
);

// Step 4: Consent
const ConsentStep = ({ data, updateField }) => (
  <div className="space-y-4">
    <h3 className="text-lg font-medium text-gray-900 mb-4">Program Consent</h3>

    <div className="bg-gray-50 rounded-lg p-6">
      <h4 className="font-medium text-gray-900 mb-3">Contingency Management Program Agreement</h4>

      <div className="space-y-3 text-sm text-gray-700">
        <p>By enrolling in this program, the patient understands and agrees to:</p>

        <ul className="list-disc list-inside space-y-2 ml-2">
          <li>Participate in regular peer support sessions</li>
          <li>Work toward mutually agreed-upon recovery goals</li>
          <li>Allow billing to Utah Medicaid for covered services</li>
          <li>Receive incentive rewards for meeting program milestones</li>
          <li>Allow program staff to coordinate care with healthcare providers</li>
          <li>Understand that participation is voluntary and can be discontinued at any time</li>
        </ul>

        <p className="mt-4">
          <strong>Privacy Notice:</strong> Your health information will be protected according to HIPAA regulations.
          Information may be shared with Medicaid for billing purposes and with your healthcare team for care coordination.
        </p>
      </div>
    </div>

    <div className="space-y-4 border-t pt-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Consent Method *
        </label>
        <select
          value={data.consentMethod}
          onChange={(e) => updateField('consentMethod', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="in_person">In Person - Verbal</option>
          <option value="written">Written Signature</option>
          <option value="electronic">Electronic Signature</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Witness Name (CPSS Staff) *
        </label>
        <input
          type="text"
          value={data.witnessName}
          onChange={(e) => updateField('witnessName', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          placeholder="Your name as witness"
          required
        />
      </div>

      <div className="flex items-center space-x-3">
        <input
          type="checkbox"
          id="consent"
          checked={data.consentGiven}
          onChange={(e) => updateField('consentGiven', e.target.checked)}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="consent" className="text-sm text-gray-700">
          Patient has provided informed consent to enroll in the Contingency Management program
        </label>
      </div>
    </div>
  </div>
);

// Step 5: Review
const ReviewStep = ({ data }) => (
  <div className="space-y-6">
    <h3 className="text-lg font-medium text-gray-900 mb-4">Review Enrollment Information</h3>

    <div className="bg-green-50 border border-green-200 rounded-md p-4">
      <div className="flex items-center">
        <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
        <span className="font-medium text-green-800">Ready to enroll in CM Program</span>
      </div>
    </div>

    <div className="space-y-4">
      <Section title="Patient Information">
        <InfoRow label="Name" value={`${data.firstName} ${data.lastName}`} />
        <InfoRow label="Medicaid ID" value={data.medicaidId} />
        <InfoRow label="Date of Birth" value={data.dob} />
      </Section>

      <Section title="Contact Information">
        <InfoRow label="Primary Phone" value={data.phone} />
        <InfoRow label="Alternative Phone" value={data.altPhone || 'Not provided'} />
        <InfoRow label="Email" value={data.email || 'Not provided'} />
        <InfoRow label="Outreach Method" value="Text Message with App Link" />
      </Section>

      <Section title="Address">
        <InfoRow label="Street" value={`${data.street} ${data.apt ? `#${data.apt}` : ''}`} />
        <InfoRow label="City, State ZIP" value={`${data.city}, ${data.state} ${data.zip}`} />
      </Section>

      <Section title="Program Details">
        <InfoRow label="Stimulant Use Status" value={data.primaryDiagnosis.replace(/_/g, ' ').replace(/^./, str => str.toUpperCase())} />
        <InfoRow label="Enrollment Location" value={data.enrollmentLocation.replace(/_/g, ' ').replace(/^./, str => str.toUpperCase())} />
        <InfoRow label="Referred By" value="Zack (USARA CPSS)" />
      </Section>

      <Section title="Consent">
        <InfoRow label="Consent Given" value={data.consentGiven ? 'Yes' : 'No'} />
        <InfoRow label="Consent Method" value={data.consentMethod.replace(/_/g, ' ')} />
        <InfoRow label="Witnessed By" value={data.witnessName} />
        <InfoRow label="Date" value={data.consentDate} />
      </Section>
    </div>

    <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
      <p className="text-sm text-blue-800">
        <strong>Next Steps:</strong> After enrollment, the patient will receive:
      </p>
      <ul className="list-disc list-inside text-sm text-blue-700 mt-2 ml-2">
        <li>Welcome packet with program details</li>
        <li>Schedule for first peer support session</li>
        <li>Information about earning incentives</li>
        <li>Contact information for their assigned CPSS</li>
      </ul>
    </div>
  </div>
);

// Helper Components
const Section = ({ title, children }) => (
  <div className="border-t pt-4">
    <h4 className="font-medium text-gray-900 mb-2">{title}</h4>
    <dl className="space-y-1">
      {children}
    </dl>
  </div>
);

const InfoRow = ({ label, value }) => (
  <div className="flex justify-between py-1">
    <dt className="text-sm text-gray-600">{label}:</dt>
    <dd className="text-sm font-medium text-gray-900">{value}</dd>
  </div>
);

export default EnrollmentFlow;