import { useState, useEffect } from 'react';
import { 
  Calendar, 
  Clock, 
  User, 
  ChevronLeft, 
  ChevronRight, 
  CheckCircle, 
  X, 
  Plus, 
  Search, 
  LogOut, 
  CalendarDays,
  ArrowRight,
  Stethoscope,
  HeartHandshake
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

interface Appointment {
  id: string;
  doctor_id: string;
  patient_id: string;
  slot_id?: string;
  date: string;
  start_time: string;
  end_time: string;
  status: string;
  doctor_name?: string;
  patient_name?: string;
  specialization?: string;
}

interface Slot {
  id: string;
  doctor_id: string;
  date: string;
  start_time: string;
  end_time: string;
  is_available: boolean;
  status: string;
}

interface Doctor {
  id: string;
  name: string;
  specialization: string;
  email: string;
  room?: string;
  next_available_slot?: string;
}

interface UserSession {
  portal: 'doctor' | 'patient';
  id: string;
  name: string;
  email?: string;
  specialization?: string;
  token: string;
}

export default function App() {
  // Authentication & Portal Session
  const [session, setSession] = useState<UserSession | null>(() => {
    const saved = localStorage.getItem('healthcare_session');
    return saved ? JSON.parse(saved) : null;
  });

  // Portal Login flow state: 'select' | 'doctor' | 'patient'
  const [loginView, setLoginView] = useState<'select' | 'doctor' | 'patient'>('select');
  const [loginIdentifier, setLoginIdentifier] = useState<string>('');
  const [loginPassword, setLoginPassword] = useState<string>('');
  const [loginError, setLoginError] = useState<string | null>(null);

  // Active navigation tab within authenticated portal
  const [activeTab, setActiveTab] = useState<string>('Overview');
  const [currentDate, setCurrentDate] = useState<string>('2026-11-06');
  
  // Data states
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [bannerMessage, setBannerMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Selected appointment modal
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const [showRescheduleModal, setShowRescheduleModal] = useState<boolean>(false);
  const [newRescheduleTime, setNewRescheduleTime] = useState<string>('11:30');

  // Availability management modal
  const [showAddSlotModal, setShowAddSlotModal] = useState<boolean>(false);
  const [newSlotTime, setNewSlotTime] = useState<string>('12:00');

  // Patient Booking Flow
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>('doc_1');
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [specializationFilter, setSpecializationFilter] = useState<string>('All');

  const notify = (text: string, type: 'success' | 'error' = 'success') => {
    setBannerMessage({ text, type });
    setTimeout(() => setBannerMessage(null), 4000);
  };

  // Sign in handler
  const handleSignIn = async (portalType: 'doctor' | 'patient', customIdentifier?: string) => {
    setLoginError(null);
    const identifier = customIdentifier || loginIdentifier || (portalType === 'doctor' ? 'doc_1' : '1042');

    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portal: portalType,
          identifier: identifier,
          password: loginPassword || 'demo'
        })
      });

      if (res.ok) {
        const data = await res.json();
        const newSession: UserSession = {
          portal: portalType,
          id: data.user.id,
          name: data.user.name,
          email: data.user.email,
          specialization: data.user.specialization,
          token: data.access_token
        };
        setSession(newSession);
        localStorage.setItem('healthcare_session', JSON.stringify(newSession));
        setActiveTab(portalType === 'doctor' ? 'Overview' : 'Home');
        notify(`Signed in to ${portalType === 'doctor' ? 'Doctor Portal' : 'Patient Portal'} as ${newSession.name}`);
      } else {
        const err = await res.json();
        setLoginError(err.detail || 'Authentication failed');
      }
    } catch {
      // Local demo fallback
      const fallbackSession: UserSession = {
        portal: portalType,
        id: portalType === 'doctor' ? 'doc_1' : 'pat_1042',
        name: portalType === 'doctor' ? 'Dr. Ananya Mehta' : 'Patient #1042',
        specialization: portalType === 'doctor' ? 'Cardiology' : undefined,
        token: `mock-${portalType}-token`
      };
      setSession(fallbackSession);
      localStorage.setItem('healthcare_session', JSON.stringify(fallbackSession));
      setActiveTab(portalType === 'doctor' ? 'Overview' : 'Home');
    }
  };

  // Sign out handler
  const handleSignOut = () => {
    localStorage.removeItem('healthcare_session');
    setSession(null);
    setLoginView('select');
    setLoginIdentifier('');
    setLoginPassword('');
    notify('Successfully signed out.');
  };

  // Fetch data
  const fetchData = async () => {
    try {
      const docRes = await fetch(`${API_BASE}/api/v1/doctors`);
      if (docRes.ok) {
        const docData = await docRes.json();
        setDoctors(docData);
      }

      const slotRes = await fetch(`${API_BASE}/api/v1/doctors/doc_1/slots?date=${currentDate}`);
      if (slotRes.ok) {
        const slotData = await slotRes.json();
        setSlots(slotData);
      }

      const aptRes = await fetch(`${API_BASE}/api/v1/appointments?date=${currentDate}`);
      if (aptRes.ok) {
        const aptData = await aptRes.json();
        setAppointments(aptData);
      }
    } catch {
      loadFallbackData();
    }
  };

  const loadFallbackData = () => {
    setDoctors([
      { id: 'doc_1', name: 'Dr. Ananya Mehta', specialization: 'Cardiology', email: 'ananya.mehta@clinic.local', room: 'Suite 4B', next_available_slot: '10:00 (2026-11-06)' },
      { id: 'doc_2', name: 'Dr. Marcus Vance', specialization: 'Cardiology', email: 'marcus.vance@clinic.local', room: 'Suite 2A', next_available_slot: '11:00 (2026-11-06)' },
      { id: 'doc_3', name: 'Dr. Sarah Lin', specialization: 'Neurology', email: 'sarah.lin@clinic.local', room: 'Suite 3C', next_available_slot: '14:00 (2026-11-06)' }
    ]);

    setSlots([
      { id: 's1', doctor_id: 'doc_1', date: '2026-11-06', start_time: '09:00', end_time: '09:30', is_available: false, status: 'Booked' },
      { id: 's2', doctor_id: 'doc_1', date: '2026-11-06', start_time: '09:30', end_time: '10:00', is_available: false, status: 'Booked' },
      { id: 's3', doctor_id: 'doc_1', date: '2026-11-06', start_time: '10:00', end_time: '10:30', is_available: true, status: 'Available' },
      { id: 's4', doctor_id: 'doc_1', date: '2026-11-06', start_time: '10:30', end_time: '11:00', is_available: false, status: 'Booked' },
      { id: 's5', doctor_id: 'doc_1', date: '2026-11-06', start_time: '11:00', end_time: '11:30', is_available: false, status: 'Booked' },
      { id: 's6', doctor_id: 'doc_1', date: '2026-11-06', start_time: '11:30', end_time: '12:00', is_available: true, status: 'Available' },
      { id: 's7', doctor_id: 'doc_1', date: '2026-11-06', start_time: '14:00', end_time: '14:30', is_available: false, status: 'Booked' },
      { id: 's8', doctor_id: 'doc_1', date: '2026-11-06', start_time: '14:30', end_time: '15:00', is_available: false, status: 'Booked' },
      { id: 's9', doctor_id: 'doc_1', date: '2026-11-06', start_time: '15:00', end_time: '15:30', is_available: true, status: 'Available' },
    ]);

    setAppointments([
      { id: 'APT-10478', doctor_id: 'doc_1', patient_id: 'pat_1014', date: '2026-11-06', start_time: '09:00', end_time: '09:30', status: 'Confirmed', patient_name: 'Patient #1014', doctor_name: 'Dr. Ananya Mehta' },
      { id: 'APT-10480', doctor_id: 'doc_1', patient_id: 'pat_1029', date: '2026-11-06', start_time: '09:30', end_time: '10:00', status: 'Confirmed', patient_name: 'Patient #1029', doctor_name: 'Dr. Ananya Mehta' },
      { id: 'APT-10482', doctor_id: 'doc_1', patient_id: 'pat_1042', date: '2026-11-06', start_time: '10:30', end_time: '11:00', status: 'Confirmed', patient_name: 'Patient #1042', doctor_name: 'Dr. Ananya Mehta' },
      { id: 'APT-10485', doctor_id: 'doc_1', patient_id: 'pat_1055', date: '2026-11-06', start_time: '11:00', end_time: '11:30', status: 'Confirmed', patient_name: 'Patient #1055', doctor_name: 'Dr. Ananya Mehta' },
      { id: 'APT-10491', doctor_id: 'doc_1', patient_id: 'pat_1088', date: '2026-11-06', start_time: '14:00', end_time: '14:30', status: 'Confirmed', patient_name: 'Patient #1088', doctor_name: 'Dr. Ananya Mehta' },
      { id: 'APT-10494', doctor_id: 'doc_1', patient_id: 'pat_1102', date: '2026-11-06', start_time: '14:30', end_time: '15:00', status: 'Confirmed', patient_name: 'Patient #1102', doctor_name: 'Dr. Ananya Mehta' },
      { id: 'APT-10499', doctor_id: 'doc_1', patient_id: 'pat_1140', date: '2026-11-06', start_time: '15:30', end_time: '16:00', status: 'Confirmed', patient_name: 'Patient #1140', doctor_name: 'Dr. Ananya Mehta' },
    ]);
  };

  useEffect(() => {
    if (session) {
      fetchData();
    }
  }, [currentDate, session]);

  // Appointment Actions
  const handleCancelAppointment = async (aptId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/appointments/${aptId}/cancel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${session?.token || 'doctor-ananya'}` }
      });
      if (res.ok) {
        notify(`Appointment #${aptId} has been cancelled and slot released.`);
        setSelectedAppointment(null);
        fetchData();
      } else {
        const err = await res.json();
        notify(err.detail || 'Failed to cancel appointment', 'error');
      }
    } catch {
      setAppointments(prev => prev.map(a => a.id === aptId ? { ...a, status: 'Cancelled' } : a));
      notify(`Appointment #${aptId} cancelled.`);
      setSelectedAppointment(null);
    }
  };

  const handleReschedule = async () => {
    if (!selectedAppointment) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/appointments/${selectedAppointment.id}/reschedule`, {
        method: 'PATCH',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.token || 'doctor-ananya'}` 
        },
        body: JSON.stringify({
          new_date: currentDate,
          new_start_time: newRescheduleTime
        })
      });

      if (res.ok) {
        notify(`Appointment rescheduled to ${newRescheduleTime}.`);
        setShowRescheduleModal(false);
        setSelectedAppointment(null);
        fetchData();
      } else {
        const err = await res.json();
        notify(err.detail || 'Conflict: Slot unavailable', 'error');
      }
    } catch {
      notify(`Rescheduled to ${newRescheduleTime} (offline mode).`);
      setShowRescheduleModal(false);
      setSelectedAppointment(null);
    }
  };

  const handleToggleSlot = async (slot: Slot) => {
    const endpoint = slot.is_available ? 'disable' : 'enable';
    try {
      const res = await fetch(`${API_BASE}/api/v1/slots/${slot.id}/${endpoint}`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${session?.token || 'doctor-ananya'}` }
      });
      if (res.ok) {
        notify(`Slot ${slot.start_time} updated.`);
        fetchData();
      }
    } catch {
      setSlots(prev => prev.map(s => s.id === slot.id ? { ...s, is_available: !s.is_available, status: !s.is_available ? 'Available' : 'Booked' } : s));
      notify(`Slot ${slot.start_time} updated.`);
    }
  };

  const handleAddSlot = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/slots`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.token || 'doctor-ananya'}`
        },
        body: JSON.stringify({
          doctor_id: session?.id || 'doc_1',
          date: currentDate,
          start_time: newSlotTime,
          end_time: `${parseInt(newSlotTime.split(':')[0])}:${parseInt(newSlotTime.split(':')[1]) + 30}`
        })
      });
      if (res.ok) {
        notify(`Added availability slot at ${newSlotTime}.`);
        setShowAddSlotModal(false);
        fetchData();
      } else {
        const err = await res.json();
        notify(err.detail || 'Slot already exists', 'error');
      }
    } catch {
      notify(`Slot ${newSlotTime} added.`);
      setShowAddSlotModal(false);
    }
  };

  const handlePatientBook = async () => {
    if (!selectedSlot) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/appointments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.token || 'patient-1042'}`
        },
        body: JSON.stringify({
          doctor_id: selectedDoctorId,
          patient_id: session?.id || 'pat_1042',
          slot_id: selectedSlot.id,
          date: selectedSlot.date,
          start_time: selectedSlot.start_time
        })
      });

      if (res.ok) {
        notify('Appointment confirmed successfully!');
        setSelectedSlot(null);
        fetchData();
      } else {
        const err = await res.json();
        notify(err.detail || 'Booking conflict: Slot taken', 'error');
      }
    } catch {
      notify('Appointment confirmed (offline mode).');
      setSelectedSlot(null);
    }
  };

  // Metrics
  const todayAppointmentsCount = appointments.filter(a => a.status === 'Confirmed').length;
  const availableSlotsCount = slots.filter(s => s.is_available).length;
  const upcomingCount = 4;

  const scheduleRows = [
    { time: '09:00', patientId: 'Patient #1014', status: 'Confirmed', isAvailable: false, aptId: 'APT-10478' },
    { time: '09:30', patientId: 'Patient #1029', status: 'Confirmed', isAvailable: false, aptId: 'APT-10480' },
    { time: '10:00', patientId: 'Available', status: 'Bookable', isAvailable: true, aptId: null },
    { time: '10:30', patientId: 'Patient #1042', status: 'Confirmed', isAvailable: false, aptId: 'APT-10482' },
    { time: '11:00', patientId: 'Patient #1055', status: 'Confirmed', isAvailable: false, aptId: 'APT-10485' },
    { time: '11:30', patientId: 'Available', status: 'Bookable', isAvailable: true, aptId: null },
    { time: '14:00', patientId: 'Patient #1088', status: 'Confirmed', isAvailable: false, aptId: 'APT-10491' },
    { time: '14:30', patientId: 'Patient #1102', status: 'Confirmed', isAvailable: false, aptId: 'APT-10494' },
    { time: '15:00', patientId: 'Available', status: 'Bookable', isAvailable: true, aptId: null },
    { time: '15:30', patientId: 'Patient #1140', status: 'Confirmed', isAvailable: false, aptId: 'APT-10499' },
  ];

  const upcomingList = [
    { date: '07 Nov 2026', time: '09:30 AM', patient: 'Patient #1014', status: 'Confirmed' },
    { date: '07 Nov 2026', time: '11:00 AM', patient: 'Patient #1042', status: 'Confirmed' },
    { date: '09 Nov 2026', time: '10:00 AM', patient: 'Patient #1055', status: 'Confirmed' },
    { date: '10 Nov 2026', time: '02:00 PM', patient: 'Patient #1088', status: 'Confirmed' },
  ];

  // ==========================================
  // UNATHENTICATED STATE: SEPARATE PORTALS & LOGIN
  // ==========================================
  if (!session) {
    return (
      <div className="login-page-container">
        {bannerMessage && (
          <div className={`feedback-banner ${bannerMessage.type}`} style={{ maxWidth: '420px', width: '100%', marginBottom: '16px' }}>
            <span>{bannerMessage.text}</span>
            <button style={{ background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setBannerMessage(null)}>
              <X size={14} />
            </button>
          </div>
        )}

        {/* 1. Portal Gateway Selector */}
        {loginView === 'select' && (
          <div className="portal-gateway-card">
            <div style={{ textAlign: 'center', marginBottom: '8px' }}>
              <span className="brand-badge">Appointment Management Service</span>
              <h1 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
                Select Your Portal
              </h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '6px' }}>
                Please choose your appropriate portal to sign in to your role-specific appointment dashboard.
              </p>
            </div>

            <div className="portal-options-grid">
              {/* Doctor Portal Box */}
              <div 
                className="portal-selection-box doctor-box"
                onClick={() => {
                  setLoginView('doctor');
                  setLoginIdentifier('ananya.mehta@clinic.local');
                }}
              >
                <div>
                  <div className="portal-icon-wrapper doctor">
                    <Stethoscope size={24} />
                  </div>
                  <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Doctor Portal
                  </h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '6px' }}>
                    Access your daily consultation schedule, manage bookable availability slots, and handle appointments.
                  </p>
                </div>
                <div style={{ marginTop: '24px', display: 'flex', alignItems: 'center', color: '#0284c7', fontWeight: 600, fontSize: '13px', gap: '6px' }}>
                  <span>Physician Sign In</span>
                  <ArrowRight size={16} />
                </div>
              </div>

              {/* Patient Portal Box */}
              <div 
                className="portal-selection-box patient-box"
                onClick={() => {
                  setLoginView('patient');
                  setLoginIdentifier('Patient #1042');
                }}
              >
                <div>
                  <div className="portal-icon-wrapper patient">
                    <HeartHandshake size={24} />
                  </div>
                  <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    Patient Portal
                  </h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '6px' }}>
                    Search medical specialists, view upcoming appointments, reschedule, or book available clinic slots.
                  </p>
                </div>
                <div style={{ marginTop: '24px', display: 'flex', alignItems: 'center', color: '#0d9488', fontWeight: 600, fontSize: '13px', gap: '6px' }}>
                  <span>Patient Sign In</span>
                  <ArrowRight size={16} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 2. Doctor Portal Login Form */}
        {loginView === 'doctor' && (
          <div className="login-form-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <div className="portal-icon-wrapper doctor" style={{ width: '36px', height: '36px', margin: 0 }}>
                <Stethoscope size={18} />
              </div>
              <div>
                <h2 style={{ fontSize: '17px', fontWeight: 700 }}>Doctor Portal Sign In</h2>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Physician Credential Access</span>
              </div>
            </div>

            {loginError && (
              <div className="feedback-banner error" style={{ fontSize: '12px', padding: '8px 12px' }}>
                {loginError}
              </div>
            )}

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                Doctor Email or ID
              </label>
              <input 
                type="text" 
                className="input-field" 
                style={{ width: '100%' }}
                placeholder="e.g. ananya.mehta@clinic.local or doc_1"
                value={loginIdentifier}
                onChange={(e) => setLoginIdentifier(e.target.value)}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                Password / Staff PIN
              </label>
              <input 
                type="password" 
                className="input-field" 
                style={{ width: '100%' }}
                placeholder="••••••••"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <span style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Quick Evaluation Presets:
              </span>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <span 
                  className="quick-account-pill"
                  onClick={() => {
                    setLoginIdentifier('ananya.mehta@clinic.local');
                    handleSignIn('doctor', 'doc_1');
                  }}
                >
                  Dr. Ananya Mehta (Cardiology)
                </span>
                <span 
                  className="quick-account-pill"
                  onClick={() => {
                    setLoginIdentifier('marcus.vance@clinic.local');
                    handleSignIn('doctor', 'doc_2');
                  }}
                >
                  Dr. Marcus Vance
                </span>
              </div>
            </div>

            <button 
              className="btn-primary" 
              style={{ width: '100%', padding: '10px', fontSize: '14px', marginBottom: '14px' }}
              onClick={() => handleSignIn('doctor')}
            >
              Sign In to Doctor Portal
            </button>

            <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--text-secondary)' }}>
              Are you a patient?{' '}
              <button 
                style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, cursor: 'pointer' }}
                onClick={() => {
                  setLoginView('patient');
                  setLoginIdentifier('Patient #1042');
                  setLoginError(null);
                }}
              >
                Switch to Patient Portal
              </button>
            </div>
          </div>
        )}

        {/* 3. Patient Portal Login Form */}
        {loginView === 'patient' && (
          <div className="login-form-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <div className="portal-icon-wrapper patient" style={{ width: '36px', height: '36px', margin: 0 }}>
                <HeartHandshake size={18} />
              </div>
              <div>
                <h2 style={{ fontSize: '17px', fontWeight: 700 }}>Patient Portal Sign In</h2>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Self-Service Scheduling Access</span>
              </div>
            </div>

            {loginError && (
              <div className="feedback-banner error" style={{ fontSize: '12px', padding: '8px 12px' }}>
                {loginError}
              </div>
            )}

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                Synthetic Patient ID
              </label>
              <input 
                type="text" 
                className="input-field" 
                style={{ width: '100%' }}
                placeholder="e.g. Patient #1042 or 1042"
                value={loginIdentifier}
                onChange={(e) => setLoginIdentifier(e.target.value)}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                Access PIN
              </label>
              <input 
                type="password" 
                className="input-field" 
                style={{ width: '100%' }}
                placeholder="••••"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <span style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                Quick Evaluation Presets:
              </span>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <span 
                  className="quick-account-pill"
                  onClick={() => {
                    setLoginIdentifier('Patient #1042');
                    handleSignIn('patient', '1042');
                  }}
                >
                  Patient #1042 (Confirmed at 10:30)
                </span>
                <span 
                  className="quick-account-pill"
                  onClick={() => {
                    setLoginIdentifier('Patient #1014');
                    handleSignIn('patient', '1014');
                  }}
                >
                  Patient #1014
                </span>
              </div>
            </div>

            <button 
              className="btn-primary" 
              style={{ width: '100%', padding: '10px', fontSize: '14px', marginBottom: '14px', backgroundColor: '#0d9488', borderColor: '#0d9488' }}
              onClick={() => handleSignIn('patient')}
            >
              Sign In to Patient Portal
            </button>

            <div style={{ textAlign: 'center', fontSize: '12px', color: 'var(--text-secondary)' }}>
              Are you a physician?{' '}
              <button 
                style={{ background: 'none', border: 'none', color: 'var(--primary)', fontWeight: 600, cursor: 'pointer' }}
                onClick={() => {
                  setLoginView('doctor');
                  setLoginIdentifier('ananya.mehta@clinic.local');
                  setLoginError(null);
                }}
              >
                Switch to Doctor Portal
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ==========================================
  // AUTHENTICATED STATE: DEDICATED PORTAL VIEW
  // ==========================================
  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="brand-badge" style={{ color: session.portal === 'doctor' ? 'var(--primary)' : '#0d9488' }}>
            {session.portal === 'doctor' ? 'Clinical Service' : 'Patient Self-Service'}
          </span>
          <h2 className="brand-title">
            {session.portal === 'doctor' ? 'Doctor Portal' : 'Patient Portal'}
          </h2>
        </div>

        <nav className="sidebar-nav">
          {session.portal === 'doctor' ? (
            <>
              <button 
                className={`nav-item ${activeTab === 'Overview' ? 'active' : ''}`}
                onClick={() => setActiveTab('Overview')}
              >
                <CalendarDays size={18} />
                Overview
              </button>
              <button 
                className={`nav-item ${activeTab === 'Schedule' ? 'active' : ''}`}
                onClick={() => setActiveTab('Schedule')}
              >
                <Clock size={18} />
                Schedule
              </button>
              <button 
                className={`nav-item ${activeTab === 'Appointments' ? 'active' : ''}`}
                onClick={() => setActiveTab('Appointments')}
              >
                <CheckCircle size={18} />
                Appointments
              </button>
              <button 
                className={`nav-item ${activeTab === 'Availability' ? 'active' : ''}`}
                onClick={() => setActiveTab('Availability')}
              >
                <Calendar size={18} />
                Availability
              </button>
              <button 
                className={`nav-item ${activeTab === 'Profile' ? 'active' : ''}`}
                onClick={() => setActiveTab('Profile')}
              >
                <User size={18} />
                Profile
              </button>
            </>
          ) : (
            <>
              <button 
                className={`nav-item ${activeTab === 'Home' ? 'active' : ''}`}
                onClick={() => setActiveTab('Home')}
              >
                <CalendarDays size={18} />
                Home
              </button>
              <button 
                className={`nav-item ${activeTab === 'Find a Doctor' ? 'active' : ''}`}
                onClick={() => setActiveTab('Find a Doctor')}
              >
                <Search size={18} />
                Find a Doctor
              </button>
              <button 
                className={`nav-item ${activeTab === 'Book Appointment' ? 'active' : ''}`}
                onClick={() => setActiveTab('Book Appointment')}
              >
                <Calendar size={18} />
                Book Appointment
              </button>
              <button 
                className={`nav-item ${activeTab === 'My Appointments' ? 'active' : ''}`}
                onClick={() => setActiveTab('My Appointments')}
              >
                <CheckCircle size={18} />
                My Appointments
              </button>
              <button 
                className={`nav-item ${activeTab === 'Profile' ? 'active' : ''}`}
                onClick={() => setActiveTab('Profile')}
              >
                <User size={18} />
                Profile
              </button>
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          <button className="nav-item" onClick={handleSignOut}>
            <LogOut size={18} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        {/* Top Header */}
        <header className="top-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
              {session.portal === 'doctor' ? 'Hospital Appointments — Doctor Portal' : 'Clinic Patient Portal'}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div className="user-profile-summary">
              <div 
                className="user-avatar"
                style={{ 
                  backgroundColor: session.portal === 'doctor' ? 'var(--primary-subtle)' : '#f0fdfa',
                  color: session.portal === 'doctor' ? 'var(--primary)' : '#0d9488',
                  borderColor: session.portal === 'doctor' ? 'var(--primary-border)' : '#99f6e4'
                }}
              >
                {session.portal === 'doctor' ? 'AM' : '10'}
              </div>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {session.name}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                  {session.portal === 'doctor' ? session.specialization || 'Physician' : 'Synthetic Patient ID'}
                </div>
              </div>
            </div>

            <button 
              className="btn-sm" 
              onClick={handleSignOut}
              title="Sign out of portal"
              style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', padding: '4px 8px' }}
            >
              <LogOut size={13} />
              <span>Sign out</span>
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="page-content">
          {bannerMessage && (
            <div className={`feedback-banner ${bannerMessage.type}`}>
              <span>{bannerMessage.text}</span>
              <button style={{ background: 'none', border: 'none', cursor: 'pointer' }} onClick={() => setBannerMessage(null)}>
                <X size={14} />
              </button>
            </div>
          )}

          {/* DOCTOR VIEW: OVERVIEW / SCHEDULE */}
          {session.portal === 'doctor' && (activeTab === 'Overview' || activeTab === 'Schedule') && (
            <>
              {/* Header */}
              <div className="page-header-banner">
                <h1 className="page-title">Good morning, {session.name.replace('Dr. ', 'Dr. ')}</h1>
                <div className="page-meta">
                  <span style={{ fontWeight: 600, color: 'var(--primary)' }}>{session.specialization || 'Cardiology'}</span>
                  <span className="meta-dot"></span>
                  <span>Friday, 06 November 2026</span>
                </div>
              </div>

              {/* Three clean summary metrics */}
              <div className="metrics-row">
                <div className="metric-card">
                  <div className="metric-val">{todayAppointmentsCount || 7}</div>
                  <div className="metric-label">Today's appointments</div>
                </div>
                <div className="metric-card">
                  <div className="metric-val">{availableSlotsCount || 3}</div>
                  <div className="metric-label">Available slots</div>
                </div>
                <div className="metric-card">
                  <div className="metric-val">{upcomingCount}</div>
                  <div className="metric-label">Upcoming</div>
                </div>
              </div>

              {/* Main Schedule Container */}
              <div className="schedule-container">
                <div className="schedule-header">
                  <h2 className="schedule-title">Today's Schedule</h2>
                  <div className="date-selector">
                    <button className="nav-arrow-btn">
                      <ChevronLeft size={16} />
                    </button>
                    <span>06 November 2026</span>
                    <button className="nav-arrow-btn">
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>

                <div className="schedule-list">
                  {scheduleRows.map((row, idx) => (
                    <div key={idx} className="schedule-row">
                      <div className="schedule-time">{row.time}</div>
                      <div className={`schedule-patient ${row.isAvailable ? 'available' : ''}`}>
                        {row.patientId}
                      </div>
                      <div className="schedule-status">
                        <span className={`status-pill ${row.isAvailable ? 'bookable' : 'confirmed'}`}>
                          {row.status}
                        </span>
                      </div>
                      <div className="schedule-actions">
                        {!row.isAvailable ? (
                          <button 
                            className="btn-sm"
                            onClick={() => setSelectedAppointment({
                              id: row.aptId || 'APT-10482',
                              doctor_id: session.id,
                              patient_id: row.patientId.replace('Patient #', 'pat_'),
                              date: '06 November 2026',
                              start_time: `${row.time} AM`,
                              end_time: '11:00 AM',
                              status: 'Confirmed',
                              patient_name: row.patientId
                            })}
                          >
                            View
                          </button>
                        ) : (
                          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>—</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Upcoming Appointments */}
              <div className="section-card">
                <h3 className="section-title">Upcoming appointments</h3>
                <table className="clean-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Time</th>
                      <th>Patient</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {upcomingList.map((item, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 500 }}>{item.date}</td>
                        <td>{item.time}</td>
                        <td>{item.patient}</td>
                        <td>
                          <span className="status-pill confirmed" style={{ fontSize: '11px', padding: '2px 8px' }}>
                            {item.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* DOCTOR VIEW: AVAILABILITY TAB */}
          {session.portal === 'doctor' && activeTab === 'Availability' && (
            <div>
              <div className="page-header-banner" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h1 className="page-title">My Availability</h1>
                  <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
                    Manage bookable time slots for patient appointments.
                  </p>
                </div>
                <button className="btn-primary" onClick={() => setShowAddSlotModal(true)}>
                  <Plus size={16} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
                  Add Slot
                </button>
              </div>

              <div className="schedule-container">
                <div className="schedule-header">
                  <div className="date-selector">
                    <button className="nav-arrow-btn">
                      <ChevronLeft size={16} />
                    </button>
                    <span>06 November 2026</span>
                    <button className="nav-arrow-btn">
                      <ChevronRight size={16} />
                    </button>
                  </div>
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                    {slots.filter(s => s.is_available).length} of {slots.length} slots bookable
                  </span>
                </div>

                <div className="schedule-list">
                  {slots.map((slot) => (
                    <div key={slot.id} className="schedule-row">
                      <div className="schedule-time">{slot.start_time}</div>
                      <div className="schedule-patient">
                        {slot.start_time} – {slot.end_time}
                      </div>
                      <div className="schedule-status">
                        <span className={`status-pill ${slot.is_available ? 'bookable' : 'confirmed'}`}>
                          {slot.is_available ? 'Available' : 'Booked'}
                        </span>
                      </div>
                      <div className="schedule-actions" style={{ width: '130px' }}>
                        <button 
                          className="btn-sm"
                          onClick={() => handleToggleSlot(slot)}
                        >
                          {slot.is_available ? 'Disable Slot' : 'Enable Slot'}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* DOCTOR VIEW: APPOINTMENTS TAB */}
          {session.portal === 'doctor' && activeTab === 'Appointments' && (
            <div className="section-card">
              <h2 className="section-title">All Appointments</h2>
              <table className="clean-table">
                <thead>
                  <tr>
                    <th>Appointment ID</th>
                    <th>Patient</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {appointments.map((apt) => (
                    <tr key={apt.id}>
                      <td style={{ fontWeight: 600, color: 'var(--primary)' }}>#{apt.id}</td>
                      <td>{apt.patient_name || `Patient #${apt.patient_id.replace('pat_', '')}`}</td>
                      <td>{apt.date}</td>
                      <td>{apt.start_time} - {apt.end_time}</td>
                      <td>
                        <span className={`status-pill ${apt.status === 'Confirmed' ? 'confirmed' : apt.status === 'Cancelled' ? 'cancelled' : 'rescheduled'}`}>
                          {apt.status}
                        </span>
                      </td>
                      <td>
                        <button className="btn-sm" onClick={() => setSelectedAppointment(apt)}>
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* DOCTOR VIEW: PROFILE */}
          {session.portal === 'doctor' && activeTab === 'Profile' && (
            <div className="section-card" style={{ maxWidth: '520px' }}>
              <h2 className="section-title">Doctor Profile</h2>
              <div className="detail-row">
                <span className="detail-label">Full Name</span>
                <span className="detail-val">{session.name}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Specialization</span>
                <span className="detail-val">{session.specialization || 'Cardiology'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Clinic Room</span>
                <span className="detail-val">Suite 4B (Cardiology West)</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Service Type</span>
                <span className="detail-val">Outpatient Appointment Service</span>
              </div>
            </div>
          )}

          {/* PATIENT VIEW: HOME */}
          {session.portal === 'patient' && activeTab === 'Home' && (
            <div>
              <div className="page-header-banner">
                <h1 className="page-title">Welcome, {session.name}</h1>
                <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Manage your clinic appointments and book consultations.
                </p>
              </div>

              {/* Primary Focus: Upcoming Appointment Card */}
              <div className="section-card" style={{ borderLeft: '4px solid #0d9488' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#0d9488', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Upcoming Appointment
                  </span>
                  <span className="status-pill confirmed">Confirmed</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '18px' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Doctor</div>
                    <div style={{ fontSize: '15px', fontWeight: 600, marginTop: '2px' }}>Dr. Ananya Mehta</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Specialization</div>
                    <div style={{ fontSize: '15px', fontWeight: 600, marginTop: '2px' }}>Cardiology</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Date</div>
                    <div style={{ fontSize: '15px', fontWeight: 600, marginTop: '2px' }}>06 November 2026</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Time</div>
                    <div style={{ fontSize: '15px', fontWeight: 600, marginTop: '2px' }}>10:30 AM</div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button 
                    className="btn-secondary"
                    onClick={() => {
                      setSelectedAppointment({
                        id: 'APT-10482',
                        doctor_id: 'doc_1',
                        patient_id: session.id,
                        date: '2026-11-06',
                        start_time: '10:30',
                        end_time: '11:00',
                        status: 'Confirmed',
                        doctor_name: 'Dr. Ananya Mehta'
                      });
                      setShowRescheduleModal(true);
                    }}
                  >
                    Reschedule
                  </button>
                  <button 
                    className="btn-danger-outline"
                    onClick={() => handleCancelAppointment('APT-10482')}
                  >
                    Cancel Appointment
                  </button>
                </div>
              </div>

              {/* Recent Appointments */}
              <div className="section-card">
                <h3 className="section-title">Recent appointments</h3>
                <table className="clean-table">
                  <thead>
                    <tr>
                      <th>Doctor</th>
                      <th>Specialization</th>
                      <th>Date</th>
                      <th>Time</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style={{ fontWeight: 600 }}>Dr. Ananya Mehta</td>
                      <td>Cardiology</td>
                      <td>24 October 2026</td>
                      <td>09:00 AM</td>
                      <td><span className="status-pill confirmed">Completed</span></td>
                    </tr>
                    <tr>
                      <td style={{ fontWeight: 600 }}>Dr. Sarah Lin</td>
                      <td>Neurology</td>
                      <td>12 September 2026</td>
                      <td>11:30 AM</td>
                      <td><span className="status-pill confirmed">Completed</span></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* PATIENT VIEW: FIND A DOCTOR & BOOK APPOINTMENT */}
          {session.portal === 'patient' && (activeTab === 'Find a Doctor' || activeTab === 'Book Appointment') && (
            <div>
              <div className="page-header-banner">
                <h1 className="page-title">Find a Doctor & Book Appointment</h1>
                <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Select a specialist and reserve an available appointment slot.
                </p>
              </div>

              {/* Search & Filters */}
              <div className="search-bar-box">
                <input 
                  type="text" 
                  className="input-field" 
                  placeholder="Search doctor name..." 
                  style={{ minWidth: '220px' }}
                />
                <select 
                  className="input-field"
                  value={specializationFilter}
                  onChange={(e) => setSpecializationFilter(e.target.value)}
                >
                  <option value="All">All Specializations</option>
                  <option value="Cardiology">Cardiology</option>
                  <option value="Neurology">Neurology</option>
                </select>
                <input 
                  type="date" 
                  className="input-field" 
                  value={currentDate} 
                  onChange={(e) => setCurrentDate(e.target.value)} 
                />
              </div>

              {/* Step 1: Doctor Results */}
              <div style={{ marginBottom: '24px' }}>
                <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-secondary)' }}>
                  1. SELECT DOCTOR
                </h3>
                {doctors
                  .filter(d => specializationFilter === 'All' || d.specialization === specializationFilter)
                  .map(doc => (
                    <div 
                      key={doc.id} 
                      className="doctor-result-card"
                      style={{ 
                        borderColor: selectedDoctorId === doc.id ? '#0d9488' : 'var(--border)',
                        boxShadow: selectedDoctorId === doc.id ? '0 0 0 1px #0d9488' : 'none'
                      }}
                    >
                      <div>
                        <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                          {doc.name}
                        </div>
                        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                          {doc.specialization} • {doc.room || 'Outpatient Clinic'}
                        </div>
                        <div style={{ fontSize: '12px', color: '#0d9488', marginTop: '4px', fontWeight: 500 }}>
                          Next available: {doc.next_available_slot || '10:00 AM (06 Nov)'}
                        </div>
                      </div>

                      <button 
                        className={`btn-sm ${selectedDoctorId === doc.id ? 'primary' : ''}`}
                        style={selectedDoctorId === doc.id ? { backgroundColor: '#0d9488', borderColor: '#0d9488' } : {}}
                        onClick={() => setSelectedDoctorId(doc.id)}
                      >
                        {selectedDoctorId === doc.id ? 'Selected' : 'View Availability'}
                      </button>
                    </div>
                  ))}
              </div>

              {/* Step 2 & 3: Select Date & Available Slot */}
              <div className="section-card">
                <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-secondary)' }}>
                  2. AVAILABLE SLOTS FOR {currentDate}
                </h3>
                
                <div className="slot-chips-grid">
                  {slots.map(slot => (
                    <button
                      key={slot.id}
                      disabled={!slot.is_available}
                      className={`slot-chip ${!slot.is_available ? 'disabled' : ''} ${selectedSlot?.id === slot.id ? 'selected' : ''}`}
                      onClick={() => setSelectedSlot(slot)}
                    >
                      {slot.start_time} {slot.is_available ? '• Available' : '• Booked'}
                    </button>
                  ))}
                </div>

                {/* Step 4: Confirmation panel */}
                {selectedSlot && (
                  <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '8px' }}>
                      3. Confirm Appointment
                    </h4>
                    <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '6px', marginBottom: '16px', fontSize: '13px' }}>
                      <div><strong>Doctor:</strong> {doctors.find(d => d.id === selectedDoctorId)?.name || 'Dr. Ananya Mehta'}</div>
                      <div><strong>Patient:</strong> {session.name}</div>
                      <div><strong>Date:</strong> {selectedSlot.date}</div>
                      <div><strong>Time:</strong> {selectedSlot.start_time} - {selectedSlot.end_time}</div>
                    </div>
                    <button 
                      className="btn-primary" 
                      style={{ backgroundColor: '#0d9488', borderColor: '#0d9488' }}
                      onClick={handlePatientBook}
                    >
                      Confirm Booking
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* PATIENT VIEW: MY APPOINTMENTS */}
          {session.portal === 'patient' && activeTab === 'My Appointments' && (
            <div className="section-card">
              <h2 className="section-title">My Appointments</h2>
              <table className="clean-table">
                <thead>
                  <tr>
                    <th>Appointment ID</th>
                    <th>Doctor</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ fontWeight: 600, color: '#0d9488' }}>#APT-10482</td>
                    <td>Dr. Ananya Mehta (Cardiology)</td>
                    <td>06 November 2026</td>
                    <td>10:30 AM</td>
                    <td><span className="status-pill confirmed">Confirmed</span></td>
                    <td>
                      <button 
                        className="btn-danger-outline" 
                        style={{ fontSize: '11px', padding: '4px 8px' }}
                        onClick={() => handleCancelAppointment('APT-10482')}
                      >
                        Cancel
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* PATIENT VIEW: PROFILE */}
          {session.portal === 'patient' && activeTab === 'Profile' && (
            <div className="section-card" style={{ maxWidth: '480px' }}>
              <h2 className="section-title">Patient Profile</h2>
              <div className="detail-row">
                <span className="detail-label">Patient Identifier</span>
                <span className="detail-val">{session.name}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Registered ID</span>
                <span className="detail-val">{session.id}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Portal Access</span>
                <span className="detail-val">Patient Portal Active</span>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* SELECTED APPOINTMENT MODAL */}
      {selectedAppointment && !showRescheduleModal && (
        <div className="modal-overlay" onClick={() => setSelectedAppointment(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Appointment #{selectedAppointment.id}</h3>
              <button className="modal-close" onClick={() => setSelectedAppointment(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="modal-body">
              <div className="detail-row">
                <span className="detail-label">Patient</span>
                <span className="detail-val">{selectedAppointment.patient_name || `Patient #${selectedAppointment.patient_id.replace('pat_', '')}`}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Doctor</span>
                <span className="detail-val">{selectedAppointment.doctor_name || 'Dr. Ananya Mehta'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Date</span>
                <span className="detail-val">{selectedAppointment.date}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Time</span>
                <span className="detail-val">{selectedAppointment.start_time}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Status</span>
                <span className="detail-val">
                  <span className={`status-pill ${selectedAppointment.status === 'Confirmed' ? 'confirmed' : 'rescheduled'}`}>
                    {selectedAppointment.status}
                  </span>
                </span>
              </div>
            </div>

            <div className="modal-footer">
              <button 
                className="btn-danger-outline"
                onClick={() => handleCancelAppointment(selectedAppointment.id)}
              >
                Cancel
              </button>
              <button 
                className="btn-primary"
                onClick={() => setShowRescheduleModal(true)}
              >
                Reschedule
              </button>
            </div>
          </div>
        </div>
      )}

      {/* RESCHEDULE MODAL */}
      {showRescheduleModal && selectedAppointment && (
        <div className="modal-overlay" onClick={() => setShowRescheduleModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Reschedule Appointment #{selectedAppointment.id}</h3>
              <button className="modal-close" onClick={() => setShowRescheduleModal(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="modal-body">
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
                Select a new available time slot for {selectedAppointment.patient_name || 'Patient'}.
              </p>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                  Target Date
                </label>
                <input 
                  type="date" 
                  className="input-field" 
                  value={currentDate} 
                  onChange={(e) => setCurrentDate(e.target.value)} 
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                  Select Available Slot
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                  {slots.filter(s => s.is_available).map(s => (
                    <button
                      key={s.id}
                      className={`slot-chip ${newRescheduleTime === s.start_time ? 'selected' : ''}`}
                      onClick={() => setNewRescheduleTime(s.start_time)}
                    >
                      {s.start_time}
                    </button>
                  ))}
                  {slots.filter(s => s.is_available).length === 0 && (
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No other open slots</span>
                  )}
                </div>
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowRescheduleModal(false)}>
                Back
              </button>
              <button className="btn-primary" onClick={handleReschedule}>
                Confirm Reschedule
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ADD SLOT MODAL */}
      {showAddSlotModal && (
        <div className="modal-overlay" onClick={() => setShowAddSlotModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Add Availability Slot</h3>
              <button className="modal-close" onClick={() => setShowAddSlotModal(false)}>
                <X size={18} />
              </button>
            </div>

            <div className="modal-body">
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                  Date
                </label>
                <input 
                  type="date" 
                  className="input-field" 
                  value={currentDate} 
                  onChange={(e) => setCurrentDate(e.target.value)} 
                  style={{ width: '100%' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>
                  Start Time (HH:MM)
                </label>
                <input 
                  type="time" 
                  className="input-field" 
                  value={newSlotTime} 
                  onChange={(e) => setNewSlotTime(e.target.value)} 
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowAddSlotModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handleAddSlot}>
                Add Slot
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
