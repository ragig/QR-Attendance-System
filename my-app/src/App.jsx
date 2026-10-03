import { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { QRCodeSVG } from 'qrcode.react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || '/api';
const api = axios.create({ baseURL: API_URL });

const getErrorMessage = (error, fallback = 'Unable to complete request') => {
  if (error.response?.data) {
    const data = error.response.data;
    if (typeof data === 'string') {
      return data.trim().startsWith('<!DOCTYPE') || data.trim().startsWith('<html')
        ? fallback
        : data;
    }
    return data.detail || data.error || Object.values(data).flat().join(' ') || fallback;
  }
  if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
    return 'Cannot reach the backend API. Start Django on port 8000, then try again.';
  }
  return error.message ? `Network error: ${error.message}` : fallback;
};

const isValidGmail = (email) => {
  const gmailPattern = /^(?=.{1,30}@gmail\.com$)(?=[a-z0-9.]*[a-z])[a-z0-9](?!.*\.\.)[a-z0-9.]*[a-z0-9]@gmail\.com$/;
  return gmailPattern.test(email);
};

const getStoredAuth = () => {
  try {
    const stored = localStorage.getItem('auth');
    return stored ? JSON.parse(stored) : null;
  } catch {
    localStorage.removeItem('auth');
    return null;
  }
};

const getUrlScanToken = () => {
  const query = new URLSearchParams(window.location.search);
  const quick = query.get('quick')?.trim();
  const attendance = query.get('attendance')?.trim();
  const token = query.get('token')?.trim();

  if (quick) {
    return { token: quick, type: 'personal' };
  }
  if (attendance) {
    return { token: attendance, type: 'session' };
  }
  if (token) {
    return { token, type: 'session' };
  }
  return { token: '', type: '' };
};

const getAppOrigin = () => {
  const currentOrigin = window.location.origin;
  const envOrigin = import.meta.env.VITE_PUBLIC_APP_URL || '';
  return envOrigin || currentOrigin;
};

const getPersonalQrValue = (qrToken) => {
  if (!qrToken) return '';
  const appOrigin = getAppOrigin();
  return `${appOrigin}/?quick=${encodeURIComponent(qrToken)}`;
};

const PersonalQrCode = ({ token, size = 180 }) => {
  const qrValue = getPersonalQrValue(token);

  return (
    <>
      <QRCodeSVG value={qrValue} size={size} />
      <p className="qr-link">Phone scan opens: {qrValue}</p>
    </>
  );
};

const getUserDisplayName = (user) => user?.display_name || user?.username || 'QR owner';

const formatDateTime = (value) => {
  if (!value) return '-';
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
};

const formatDays = (record) => {
  if (record?.days_present != null) {
    return record.days_present;
  }
  return record?.status === 'absent' ? 0 : '-';
};

const formatHours = (value) => {
  if (value == null || Number.isNaN(Number(value))) return '-';
  return `${Number(value).toFixed(2)} hr`;
};

function App() {
  const [auth, setAuth] = useState(getStoredAuth);
  const [page, setPage] = useState('home');
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    role: 'employee',
    display_name: '',
    department: '',
    employee_id: '',
    phone: '',
  });
  const [attendanceToken, setAttendanceToken] = useState('');
  const [dashboard, setDashboard] = useState(null);
  const [notices, setNotices] = useState([]);
  const [token, setToken] = useState(() => getStoredAuth()?.access || '');
  const [history, setHistory] = useState([]);
  const [historyPeriod, setHistoryPeriod] = useState('all');
  const [historySearch, setHistorySearch] = useState('');
  const [historySortField, setHistorySortField] = useState('check_in');
  const [historySortDirection, setHistorySortDirection] = useState('desc');
  const [selectedRole, setSelectedRole] = useState('employees');
  const [attendanceRole, setAttendanceRole] = useState('employees');
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedUserHistory, setSelectedUserHistory] = useState([]);
  const [selectedUserLoading, setSelectedUserLoading] = useState(false);
  const [attendanceSuccess, setAttendanceSuccess] = useState(false);
  const [activeAttendanceId, setActiveAttendanceId] = useState(null);
  const [pendingAttendanceToken, setPendingAttendanceToken] = useState('');
  const [quickLoginLoading, setQuickLoginLoading] = useState(false);
  const [quickScanResult, setQuickScanResult] = useState(null);
  const [message, setMessage] = useState('');
  const [authSubmitting, setAuthSubmitting] = useState(false);
  const [attendanceSubmitting, setAttendanceSubmitting] = useState(false);
  const [adminForm, setAdminForm] = useState({
    username: '',
    email: '',
    password: '',
    role: 'employee',
    display_name: '',
    department: '',
    employee_id: '',
    phone: '',
  });
  const [adminSubmitting, setAdminSubmitting] = useState(false);
  const [noticeForm, setNoticeForm] = useState({ recipient: '', message: '' });
  const [noticeSubmitting, setNoticeSubmitting] = useState(false);
  const [showRegisterSection, setShowRegisterSection] = useState(false);
  const [showNoticeSection, setShowNoticeSection] = useState(false);
  const [showNoticePanel, setShowNoticePanel] = useState(false);
  const toggleNoticePanel = async () => {
    if (!showNoticePanel) {
      await loadNotices(token);
    }
    setShowNoticePanel((visible) => !visible);
  };
  const [editingNoticeId, setEditingNoticeId] = useState(null);
  const [editingNoticeMessage, setEditingNoticeMessage] = useState('');

  const isManager = auth?.user?.role === 'manager';
  const isAdmin = auth?.user?.role === 'admin';
  const isEmployee = auth?.user?.role === 'employee';
  const canMarkOwnAttendance = isEmployee || isManager;

  const authHeaders = useCallback((accessToken = token) => ({ Authorization: `Bearer ${accessToken}` }), [token]);

  const loadDashboard = useCallback(async (accessToken) => {
    try {
      const { data } = await api.get('/dashboard/', { headers: authHeaders(accessToken) });
      setDashboard(data);
    } catch (error) {
      setMessage(getErrorMessage(error, 'Unable to load dashboard'));
    }
  }, [authHeaders]);

  const loadNotices = useCallback(async (accessToken) => {
    try {
      const { data } = await api.get('/notices/', { headers: authHeaders(accessToken) });
      setNotices(data);
    } catch (error) {
      setMessage(getErrorMessage(error, 'Unable to load notices'));
    }
  }, [authHeaders]);

  const loadHistory = useCallback(async (accessToken) => {
    try {
      const params = { period: historyPeriod };
      if (isAdmin) {
        params.role = attendanceRole === 'managers' ? 'manager' : 'employee';
        if (selectedUser?.user_id) {
          params.employee = selectedUser.user_id;
        }
      }
      const { data } = await api.get('/attendance/history/', {
        headers: authHeaders(accessToken),
        params,
      });
      setHistory(data);
    } catch (error) {
      setMessage(getErrorMessage(error, 'Unable to load attendance history'));
    }
  }, [authHeaders, historyPeriod, isAdmin, selectedRole, selectedUser?.user_id]);

  const loadUserHistory = useCallback(async (accessToken, userId) => {
    if (!userId) {
      setSelectedUserHistory([]);
      return;
    }
    setSelectedUserLoading(true);
    try {
      const { data } = await api.get('/attendance/history/', {
        headers: authHeaders(accessToken),
        params: { period: 'monthly', status: 'all', employee: userId },
      });
      setSelectedUserHistory(data);
    } catch (error) {
      setMessage(getErrorMessage(error, 'Unable to load user attendance history'));
      setSelectedUserHistory([]);
    } finally {
      setSelectedUserLoading(false);
    }
  }, [authHeaders]);

  const handleSelectUser = useCallback((user) => {
    setSelectedUser(user);
    setSelectedUserHistory([]);
  }, []);

  const refreshAuthedData = useCallback((accessToken) => {
    loadDashboard(accessToken);
    loadNotices(accessToken);
    loadHistory(accessToken);
  }, [loadDashboard, loadHistory, loadNotices]);

  const submitAttendanceToken = useCallback(async (rawToken = '', accessToken = token) => {
    const tokenToMark = rawToken?.trim();

    setAttendanceSubmitting(true);
    setAttendanceSuccess(false);
    try {
      const payload = tokenToMark ? { token: tokenToMark } : {};
      const { data } = await api.post('/attendance/mark/', payload, { headers: authHeaders(accessToken) });
      setMessage(data.detail || 'Attendance update complete');
      setActiveAttendanceId(data.record || null);
      setAttendanceToken('');
      setAttendanceSuccess(true);
      setQuickScanResult({
        action: 'check-in',
        status: 'success',
        detail: data.detail || 'Attendance marked successfully',
      });
      loadHistory(accessToken);
      loadDashboard(accessToken);
      try {
        window.localStorage.setItem('attendance-updated', `${Date.now()}`);
      } catch {
        // ignore storage failures
      }
      return { success: true, data };
    } catch (error) {
      const detail = getErrorMessage(error, 'Unable to mark attendance');
      setMessage(detail);
      const errorDetail = error.response?.data?.detail || '';
      if (errorDetail.includes('Already checked in')) {
        setQuickScanResult({
          action: 'already-checked-in',
          status: 'pending',
          detail,
        });
      } else if (errorDetail.includes('Attendance already recorded for this session')) {
        setQuickScanResult({
          action: 'completed',
          status: 'success',
          detail,
        });
      } else {
        setQuickScanResult({
          action: 'error',
          status: 'error',
          detail,
        });
      }
      return { success: false, error };
    } finally {
      setAttendanceSubmitting(false);
    }
  }, [authHeaders, loadDashboard, loadHistory, token]);

  const submitPendingAttendance = useCallback(async (accessToken) => {
    if (!pendingAttendanceToken) return { success: false };

    const result = await submitAttendanceToken(pendingAttendanceToken, accessToken);
    setPendingAttendanceToken('');
    setPage('scan');
    return result;
  }, [pendingAttendanceToken, submitAttendanceToken]);

  const saveAuth = useCallback(async (data, nextMessage, options = {}) => {
    localStorage.setItem('auth', JSON.stringify(data));
    setAuth(data);
    setToken(data.access);
    setMessage(nextMessage);
    if (!options.keepAttendanceToken) {
      setAttendanceToken('');
    }
    refreshAuthedData(data.access);
    if (pendingAttendanceToken) {
      await submitPendingAttendance(data.access);
    }
  }, [refreshAuthedData, pendingAttendanceToken, submitPendingAttendance]);

  useEffect(() => {
    const { token: scannedToken, type: scannedType } = getUrlScanToken();
    if (!scannedToken) return;
    window.history.replaceState(null, '', window.location.pathname);

    const loginFromPersonalQr = async () => {
      setQuickLoginLoading(true);
      setQuickScanResult(null);
      setAttendanceToken(scannedToken);
      setPage('scan');

      try {
        const { data } = await api.post('/auth/qr-login/', { qr_token: scannedToken });
        const ownerName = data.user.display_name || data.user.username || 'QR owner';
        const employeeId = data.user.employee_id || '';
        await saveAuth(data, `Verified ${ownerName}. Updating attendance...`, { keepAttendanceToken: true });

        if (data.active_attendance) {
          setActiveAttendanceId(data.active_attendance);
          setAttendanceSuccess(false);
          setQuickScanResult({
            ownerName,
            employeeId,
            action: 'already-checked-in',
            status: 'pending',
            detail: 'Attendance is already marked.',
          });
          setMessage(`${ownerName} is already checked in.`);
        } else {
          const markResponse = await api.post(
            '/attendance/mark/',
            { token: scannedToken },
            { headers: authHeaders(data.access) },
          );
          setActiveAttendanceId(markResponse.data?.record || null);
          setAttendanceSuccess(true);
          setQuickScanResult({
            ownerName,
            employeeId,
            action: 'check-in',
            status: 'success',
            detail: markResponse.data?.detail || 'Checked in successfully',
          });
          setMessage(`${ownerName} checked in successfully.`);
        }

        setAttendanceToken('');
        loadHistory(data.access);
        loadDashboard(data.access);
      } catch (error) {
        const detail = getErrorMessage(error, 'Invalid QR token. Ask your admin for a fresh QR code.');
        setQuickScanResult({
          ownerName: '',
          employeeId: '',
          action: 'error',
          status: 'error',
          detail,
        });
        setMessage(detail);
      } finally {
        setQuickLoginLoading(false);
      }
    };

    const processSessionAttendance = async () => {
      if (auth?.access) {
        setMessage('Attendance QR loaded. Verifying session token...');
        await submitAttendanceToken(scannedToken, auth.access);
        setPage('scan');
        return;
      }
      setPendingAttendanceToken(scannedToken);
      setMessage('Attendance session QR loaded. Login to mark attendance.');
      setPage('auth');
    };

    if (scannedType === 'personal') {
      loginFromPersonalQr();
    } else {
      processSessionAttendance();
    }
  }, [auth?.access, authHeaders, loadDashboard, loadHistory, saveAuth, submitAttendanceToken]);

  const submitNotice = useCallback(async () => {
    const recipient = parseInt(noticeForm.recipient, 10);
    const message = noticeForm.message.trim();
    if (!recipient || !message) {
      setMessage('Select a recipient and enter a notice message.');
      return;
    }

    setNoticeSubmitting(true);
    try {
      await api.post('/notices/', { recipient, message }, { headers: authHeaders() });
      setMessage('Notice sent successfully');
      setNoticeForm({ recipient: '', message: '' });
      loadDashboard(token);
      loadNotices(token);
    } catch (error) {
      setMessage(getErrorMessage(error, 'Unable to send notice'));
    } finally {
      setNoticeSubmitting(false);
    }
  }, [authHeaders, loadDashboard, loadNotices, noticeForm, token]);

  const submitNoticeEdit = useCallback(async () => {
    if (!editingNoticeId) return;
    const message = editingNoticeMessage.trim();
    if (!message) {
      setMessage('Enter a notice message before saving.');
      return;
    }

    setNoticeSubmitting(true);
    try {
      await api.patch(`/notices/${editingNoticeId}/`, { message }, { headers: authHeaders() });
      setMessage('Notice updated successfully');
      setEditingNoticeId(null);
      setEditingNoticeMessage('');
      loadDashboard(token);
      loadNotices(token);
    } catch (error) {
      setMessage(getErrorMessage(error, 'Unable to update notice'));
    } finally {
      setNoticeSubmitting(false);
    }
  }, [authHeaders, editingNoticeId, editingNoticeMessage, loadDashboard, loadNotices, token]);

  useEffect(() => {
    if (auth?.access) {
      const refreshTimer = window.setTimeout(() => refreshAuthedData(auth.access), 0);
      return () => window.clearTimeout(refreshTimer);
    }
    return undefined;
  }, [auth?.access, refreshAuthedData]);

  useEffect(() => {
    if (auth?.access) {
      const refreshTimer = window.setTimeout(() => loadHistory(auth.access), 0);
      return () => window.clearTimeout(refreshTimer);
    }
    return undefined;
  }, [auth?.access, loadHistory, historyPeriod]);

  useEffect(() => {
    if (!auth?.access || !selectedUser) return undefined;
    const refreshTimer = window.setTimeout(() => loadUserHistory(auth.access, selectedUser.user_id), 0);
    return () => window.clearTimeout(refreshTimer);
  }, [auth?.access, loadUserHistory, selectedUser]);

  useEffect(() => {
    if (!auth?.access) return undefined;

    const onFocus = () => {
      loadDashboard(auth.access);
      loadNotices(auth.access);
      loadHistory(auth.access);
    };
    const onStorage = (event) => {
      if (event.key === 'attendance-updated') {
        loadDashboard(auth.access);
        loadNotices(auth.access);
        loadHistory(auth.access);
      }
    };
    const interval = window.setInterval(() => {
      loadDashboard(auth.access);
      loadNotices(auth.access);
      loadHistory(auth.access);
    }, 15000);
    window.addEventListener('focus', onFocus);
    window.addEventListener('storage', onStorage);
    return () => {
      window.removeEventListener('focus', onFocus);
      window.removeEventListener('storage', onStorage);
      window.clearInterval(interval);
    };
  }, [auth?.access, loadDashboard, loadHistory, loadNotices]);

  useEffect(() => {
    if (notices?.length > 0) {
      setShowNoticePanel(true);
    }
  }, [notices?.length]);

  const handleAuth = async (event) => {
    event.preventDefault();
    const email = form.email.trim();
    if (mode === 'register' && !isValidGmail(email)) {
      setMessage('Enter a valid Gmail address using lowercase letters and numbers before @gmail.com.');
      return;
    }

    const endpoint = mode === 'login'
      ? '/auth/login/'
      : '/auth/register/';
    const body = mode === 'login'
      ? { employee_id: form.employee_id.trim(), password: form.password }
      : {
        username: form.username.trim(),
        email,
        password: form.password,
        role: form.role,
        display_name: form.display_name.trim(),
        department: form.department.trim(),
        employee_id: form.employee_id.trim(),
        phone: form.phone.trim(),
      };

    setAuthSubmitting(true);
    try {
      const { data } = await api.post(endpoint, body);
      saveAuth(data, mode === 'login' ? 'Welcome back!' : 'Account created successfully');
    } catch (error) {
      setMessage(getErrorMessage(error));
    } finally {
      setAuthSubmitting(false);
    }
  };

  const handleAdminRegister = async (event) => {
    event.preventDefault();
    setMessage('');
    
    // Validate required fields
    if (!adminForm.display_name.trim()) {
      setMessage('Display Name is required');
      return;
    }
    if (!adminForm.email.trim()) {
      setMessage('Email is required');
      return;
    }
    if (!isValidGmail(adminForm.email)) {
      setMessage('Email must be a valid Gmail address (lowercase letters and numbers only before @gmail.com)');
      return;
    }
    if (!adminForm.password) {
      setMessage('Password is required');
      return;
    }
    
    setAdminSubmitting(true);
    try {
      const { data } = await api.post('/auth/register/', adminForm, { headers: authHeaders() });
      setMessage(`✓ Created ${data.user.role} account for ${data.user.display_name || data.user.username}`);
      setAdminForm({
        username: '',
        email: '',
        password: '',
        role: 'employee',
        display_name: '',
        department: '',
        employee_id: '',
        phone: '',
      });
      loadDashboard(token);
    } catch (error) {
      const errMsg = getErrorMessage(error, 'Unable to create account');
      setMessage(`✗ Error: ${errMsg}`);
      console.error('Registration error:', error);
    } finally {
      setAdminSubmitting(false);
    }
  };
  const markAttendance = useCallback(async () => {
    await submitAttendanceToken(attendanceToken || auth?.user?.qr_token || '');
  }, [attendanceToken, auth?.user?.qr_token, submitAttendanceToken]);

  const exportReport = async () => {
    try {
      const { data } = await api.get('/reports/export/', {
        headers: authHeaders(),
        responseType: 'blob',
      });
      const url = URL.createObjectURL(data);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'attendance_report.csv';
      link.click();
      URL.revokeObjectURL(url);
      setMessage('Report exported');
    } catch (error) {
      setMessage(getErrorMessage(error, 'Unable to export report'));
    }
  };

  const checkout = async () => {
    try {
      const payload = activeAttendanceId ? { record: activeAttendanceId } : null;
      const { data } = await api.post('/attendance/checkout/', payload, { headers: authHeaders() });
      setMessage(data.detail || 'Checked out successfully');
      setActiveAttendanceId(null);
      setAttendanceSuccess(false);
      loadHistory(token);
      loadDashboard(token);
    } catch (error) {
      setMessage(getErrorMessage(error, 'Unable to check out'));
    }
  };

  const quickCheckout = async () => {
    setAttendanceSubmitting(true);
    try {
      const payload = activeAttendanceId ? { record: activeAttendanceId } : null;
      const { data } = await api.post('/attendance/checkout/', payload, { headers: authHeaders() });
      const ownerName = quickScanResult?.ownerName || getUserDisplayName(auth?.user);
      const employeeId = quickScanResult?.employeeId || auth?.user?.employee_id || '';
      setActiveAttendanceId(null);
      setAttendanceSuccess(false);
      setQuickScanResult({
        ownerName,
        employeeId,
        action: 'check-out',
        status: 'success',
        detail: data.detail || 'Checked out successfully',
      });
      setMessage(`${ownerName} checked out successfully.`);
      loadHistory(token);
      loadDashboard(token);
      try {
        window.localStorage.setItem('attendance-updated', `${Date.now()}`);
      } catch {
        // ignore storage failures
      }
    } catch (error) {
      const detail = getErrorMessage(error, 'Unable to check out');
      setQuickScanResult((current) => ({
        ...(current || {}),
        action: 'error',
        status: 'error',
        detail,
      }));
      setMessage(detail);
    } finally {
      setAttendanceSubmitting(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('auth');
    setAuth(null);
    setToken('');
    setDashboard(null);
    setHistory([]);
    setPage('home');
    setAttendanceToken('');
    setActiveAttendanceId(null);
    setQuickScanResult(null);
    setMessage('Logged out');
    if (page === 'scan' && typeof window !== 'undefined' && window.close) {
      window.close();
    }
  };

  const goHome = () => {
    setMessage('');
    setPage('home');
  };

  const summary = dashboard?.summary || {};
  const selectedRoleUsers = useMemo(() => {
    const employees = dashboard?.employees || [];
    const completeEmployees = employees.filter((employee) => (
      employee.department?.trim() || employee.phone?.trim()
    ));
    if (!isAdmin) return completeEmployees;
    return selectedRole === 'managers' ? dashboard?.managers || [] : completeEmployees;
  }, [dashboard?.employees, dashboard?.managers, isAdmin, selectedRole]);

  const attendanceRoleUsers = useMemo(() => {
    const employees = dashboard?.employees || [];
    const completeEmployees = employees.filter((employee) => (
      employee.department?.trim() || employee.phone?.trim()
    ));
    if (!isAdmin) return completeEmployees;
    return attendanceRole === 'managers' ? dashboard?.managers || [] : completeEmployees;
  }, [dashboard?.employees, dashboard?.managers, isAdmin, attendanceRole]);

  const selectedUserAttendanceTotals = useMemo(() => {
    if (!selectedUserHistory?.length) {
      return { months: 0, days: 0, hours: 0 };
    }
    const days = selectedUserHistory.reduce((sum, record) => sum + Number(record.days_present || 0), 0);
    const hours = selectedUserHistory.reduce((sum, record) => sum + Number(record.hours || 0), 0);
    return { months: selectedUserHistory.length, days, hours };
  }, [selectedUserHistory]);

  const employeeHistoryDays = useMemo(() => {
    if (!history?.length) return 0;
    const distinctDays = new Set();
    history.forEach((record) => {
      if (record.check_in) {
        distinctDays.add(new Date(record.check_in).toDateString());
      }
    });
    return distinctDays.size;
  }, [history]);

  const employeeHistoryHours = useMemo(() => {
    if (!history?.length) return 0;
    return history.reduce((sum, record) => sum + Number(record.hours || 0), 0);
  }, [history]);

  const visibleHistory = useMemo(() => {
    const searchTerm = historySearch.trim().toLowerCase();
    const filtered = history.filter((record) => {
      if (!searchTerm) return true;
      const employeeName = (record.employee_name || auth?.user?.display_name || auth?.user?.username || '').toLowerCase();
      return employeeName.includes(searchTerm);
    });

    const sorted = [...filtered].sort((a, b) => {
      const getValue = (record) => {
        switch (historySortField) {
          case 'employee':
            return (record.employee_name || '').toLowerCase();
          case 'role':
            return (record.employee_role || '').toLowerCase();
          case 'session':
            return (record.session_title || '').toLowerCase();
          case 'status':
            return (record.status || '').toLowerCase();
          case 'days':
            return Number(record.days_present) || 0;
          case 'check_out':
            return record.check_out ? new Date(record.check_out).getTime() : 0;
          case 'hours':
            return Number(record.hours) || 0;
          case 'check_in':
          default:
            return record.check_in ? new Date(record.check_in).getTime() : 0;
        }
      };

      const aValue = getValue(a);
      const bValue = getValue(b);
      if (aValue < bValue) return historySortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return historySortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [auth?.user?.display_name, auth?.user?.username, history, historySearch, historySortField, historySortDirection]);

  const handleHistorySort = (field) => {
    if (historySortField === field) {
      setHistorySortDirection((current) => (current === 'asc' ? 'desc' : 'asc'));
      return;
    }
    setHistorySortField(field);
    setHistorySortDirection('asc');
  };

  const openAuthPage = (nextMode) => {
    setMode(nextMode);
    setMessage('');
    setPage('auth');
  };

  const isMonthlyReport = historyPeriod === 'monthly';

  const attendanceRecordsSection = (
    <section className="card">
      <h2>{isAdmin ? 'Attendance records' : isManager ? 'Monthly attendance report (days present)' : 'Attendance history'}</h2>
      {(isManager || isAdmin || isEmployee) && (
        <div className="report-controls">
          <label>
            Period
            <select value={historyPeriod} onChange={(e) => setHistoryPeriod(e.target.value)}>
              <option value="all">All</option>
              <option value="daily">Daily</option>
              <option value="monthly">Monthly</option>
            </select>
          </label>
          {isAdmin && (
            <>
              <label>
                Staff type
                <select
                  value={attendanceRole}
                  onChange={(e) => {
                    setAttendanceRole(e.target.value);
                    setSelectedUser(null);
                    setSelectedUserHistory([]);
                  }}
                >
                  <option value="employees">Employees</option>
                  <option value="managers">Managers</option>
                </select>
              </label>
              <label>
                Individual
                <select
                  value={selectedUser?.user_id || ''}
                  onChange={(e) => {
                    const nextUser = attendanceRoleUsers.find((user) => `${user.user_id}` === e.target.value) || null;
                    setSelectedUser(nextUser);
                    setSelectedUserHistory([]);
                  }}
                >
                  <option value="">All {attendanceRole}</option>
                  {attendanceRoleUsers.map((user) => (
                    <option key={user.user_id} value={user.user_id}>
                      {user.display_name || user.username} {user.employee_id ? `(${user.employee_id})` : ''}
                    </option>
                  ))}
                </select>
              </label>
            </>
          )}
        </div>
      )}
      {(isManager || isAdmin) && (
        <div className="history-controls">
          <label>
            Search attendance
            <input type="search" placeholder="Search by name" value={historySearch} onChange={(e) => setHistorySearch(e.target.value)} />
          </label>
        </div>
      )}
      {visibleHistory.length > 0 ? (
        <div className="table-wrap">
          <table className="history-table">
            <thead>
              <tr>
                <th onClick={() => handleHistorySort('session')} className="sortable">{isMonthlyReport ? 'Month' : 'Details'}</th>
                <th onClick={() => handleHistorySort('employee')} className="sortable">Name</th>
                <th onClick={() => handleHistorySort('status')} className="sortable">Status</th>
                {isMonthlyReport && <th onClick={() => handleHistorySort('days')} className="sortable">Days</th>}
                {!isMonthlyReport && <th onClick={() => handleHistorySort('check_in')} className="sortable">Check In</th>}
                {!isMonthlyReport && <th onClick={() => handleHistorySort('check_out')} className="sortable">Check Out</th>}
                <th onClick={() => handleHistorySort('hours')} className="sortable">Hours</th>
              </tr>
            </thead>
            <tbody>
              {visibleHistory.map((record) => (
                <tr key={record.id}>
                  <td>{record.session_title || 'Personal check-in'}</td>
                  <td>{record.employee_name || auth.user?.display_name || auth.user?.username}</td>
                  <td>{record.status}</td>
                  {isMonthlyReport && <td>{formatDays(record)}</td>}
                  {!isMonthlyReport && <td>{formatDateTime(record.check_in)}</td>}
                  {!isMonthlyReport && <td>{formatDateTime(record.check_out)}</td>}
                  <td>{formatHours(record.hours)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="hint">No attendance records yet.</p>
      )}
    </section>
  );

  return (
    <div className="app-shell">
      <div className="top-nav">
        <span className="site-brand"><span className="brand-mark" aria-hidden="true">QR</span>QR Attendance</span>
        <div className="top-nav-actions">
          {page !== 'home' && page !== 'auth' && page !== 'scan' && (
            <button type="button" className="home-link" onClick={goHome}>Home page</button>
          )}
          {auth && page !== 'home' && (
            <button type="button" className="logout-button" onClick={logout}>Logout</button>
          )}
        </div>
      </div>
      {page === 'home' ? (
        <main className="home-page">
          <section className="home-panel">
            <div className="home-visual" aria-hidden="true">
              <span />
              <span />
              <span />
              <span />
            </div>
            <h1>QR Attendance System</h1>
            <p className="home-copy">Use your account to mark attendance, view history, and manage staff.</p>
            <div className="home-actions">
              <button type="button" onClick={() => openAuthPage('login')}>Login</button>
            </div>
            <p className="hint">Employee and manager accounts must be created by an admin.</p>
          </section>
        </main>
      ) : !auth ? (
        <section className="card auth-card">
          {quickLoginLoading && <p className="message">Opening your QR attendance page...</p>}
          <form onSubmit={handleAuth}>
            <input placeholder="Employee ID" value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })} />
            <input type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
            <button type="submit" disabled={authSubmitting}>{authSubmitting ? 'Logging in...' : 'Login'}</button>
          </form>
          {pendingAttendanceToken && (
            <p className="hint">Attendance session QR loaded. Log in to mark your check-in / check-out.</p>
          )}
          <p className="hint">Accounts must be created by an admin. Contact your administrator if you do not have login credentials.</p>
          {message && <p className="message">{message}</p>}
        </section>
      ) : page === 'scan' ? (
        <main className="scan-page">
          <section className="card scan-result-card">
            <div className="attendance-result-header">
              <div>
                <p className="attendance-result-label">Attendance scan</p>
                <h2>{quickScanResult?.ownerName || getUserDisplayName(auth.user)}</h2>
              </div>
              <span className={`status-badge ${quickScanResult?.action === 'check-in' || quickScanResult?.action === 'check-out' || quickScanResult?.action === 'completed' ? 'status-success' : quickScanResult?.status === 'pending' ? 'status-pending' : 'status-error'}`}>
                {quickScanResult?.action === 'check-in' && 'Checked in ✓'}
                {quickScanResult?.action === 'already-checked-in' && 'Checked in'}
                {quickScanResult?.action === 'check-out' && 'Checked out ✓'}
                {quickScanResult?.action === 'completed' && 'Completed ✓'}
                {quickScanResult?.action === 'error' && 'Error'}
                {!quickScanResult && 'Processing...'}
              </span>
            </div>
            <p className="attendance-result-detail">{quickScanResult?.detail || message || 'Finalizing attendance...'}</p>
            {quickScanResult?.action === 'already-checked-in' && activeAttendanceId && (
              <button
                type="button"
                className="checkout-button"
                onClick={quickCheckout}
                disabled={attendanceSubmitting || quickLoginLoading}
              >
                Check Out
              </button>
            )}
          </section>
        </main>
      ) : (
        <>
          <section className="card stats-grid">
            {(isManager || isEmployee) ? (
              <>
                <div>
                  <h3>Name</h3>
                  <p>{auth.user?.display_name || auth.user?.username}</p>
                </div>
                <div>
                  <h3>Role</h3>
                  <p>{auth.user?.role}</p>
                </div>
                <div>
                  <h3>Notices</h3>
                  <p>{summary.notices ?? 0}</p>
                </div>
                <div>
                  <h3>Present</h3>
                  <p>{`${(isEmployee ? summary.records : summary.attendanceRecords) ?? 0} days`}</p>
                </div>
              </>
            ) : (
              <>
                <div>
                  <h3>Signed in as</h3>
                  <p>{auth.user?.display_name || auth.user?.username}</p>
                </div>
                <div>
                  <h3>Role</h3>
                  <p>{auth.user?.role}</p>
                </div>
              </>
            )}
            {isAdmin && (
              <>
                <div>
                  <h3>Total employees</h3>
                  <p>{summary.employees ?? '-'}</p>
                </div>
                <div>
                  <h3>Total managers</h3>
                  <p>{summary.managers ?? '-'}</p>
                </div>
                <div>
                  <h3>Total staff</h3>
                  <p>{typeof summary.employees === 'number' && typeof summary.managers === 'number'
                    ? summary.employees + summary.managers
                    : '-'}
                  </p>
                </div>
              </>
            )}
            {isManager && (
              <>
                <div>
                  <h3>Total employees</h3>
                  <p>{summary.employees ?? '-'}</p>
                </div>
                <div>
                  <h3>Managed employees</h3>
                  <p>{summary.employees ?? '-'}</p>
                </div>
              </>
            )}
          </section>

          {isAdmin && (
            <section className="card staff-details-card">
              <div className="staff-details-header">
                <div>
                  <h2>Staff details</h2>
                  <p className="hint">View staff profiles and monthly attendance by role.</p>
                </div>
                <label className="staff-role-filter">
                  Sort by
                  <select
                    value={selectedRole}
                    onChange={(e) => {
                      setSelectedRole(e.target.value);
                      setSelectedUser(null);
                      setSelectedUserHistory([]);
                    }}
                  >
                    <option value="employees">Employees</option>
                    <option value="managers">Managers</option>
                  </select>
                </label>
              </div>
              {selectedRoleUsers.length > 0 ? (
                <div className="table-wrap staff-table-wrap">
                  <table className="employee-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Employee ID</th>
                        <th>Department</th>
                        <th>Email</th>
                        <th>Phone</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedRoleUsers.map((employee) => (
                        <tr
                          key={employee.id}
                          className={selectedUser?.user_id === employee.user_id ? 'selected-row' : ''}
                          onClick={() => handleSelectUser(employee)}
                        >
                          <td>{employee.display_name || employee.username}</td>
                          <td>{employee.employee_id || '-'}</td>
                          <td>{employee.department || '-'}</td>
                          <td>{employee.email || '-'}</td>
                          <td>
                            {employee.phone || '-'}
                            {employee.phone && (
                              <button
                                type="button"
                                className="contact-button compact"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  navigator.clipboard.writeText(employee.phone)
                                    .then(() => setMessage(`Phone number copied: ${employee.phone}`))
                                    .catch(() => setMessage('Unable to copy phone number'));
                                }}
                              >
                                Contact now
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="hint">No users available for the selected role.</p>
              )}
              {(selectedUser || selectedUserHistory.length > 0) && (
                <div className="user-attendance-panel">
                  <h3>Attendance for {selectedUser ? (selectedUser.display_name || selectedUser.username) : 'selected user'}</h3>
                  {selectedUserLoading ? (
                    <p>Loading attendance records...</p>
                  ) : selectedUserHistory.length > 0 ? (
                    <>
                      <div className="attendance-summary-row">
                        <div>
                          <h4>Months</h4>
                          <p>{selectedUserAttendanceTotals.months}</p>
                        </div>
                        <div>
                          <h4>Days present</h4>
                          <p>{selectedUserAttendanceTotals.days}</p>
                        </div>
                        <div>
                          <h4>Total hours</h4>
                          <p>{formatHours(selectedUserAttendanceTotals.hours)}</p>
                        </div>
                      </div>
                      <div className="table-wrap">
                        <table className="history-table">
                          <thead>
                            <tr>
                              <th>Month</th>
                              <th>Days</th>
                              <th>Hours</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedUserHistory.map((record) => (
                              <tr key={record.id}>
                                <td>{record.session_title || 'Monthly'}</td>
                                <td>{formatDays(record)}</td>
                                <td>{formatHours(record.hours)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  ) : (
                    <p className="hint">Select a staff member to view their monthly attendance details.</p>
                  )}
                </div>
              )}
            </section>
          )}

          {isAdmin && attendanceRecordsSection}

          <section className="card">
            <h2>Quick actions</h2>
            {message && <p className="message">{message}</p>}
            {quickScanResult && (
              <div className={`attendance-result-card ${quickScanResult.status === 'error' ? 'attendance-error' : ''}`}>
                <div className="attendance-result-header">
                  <div>
                    <p className="attendance-result-label">Attendance result for</p>
                    <h3>{quickScanResult.ownerName || getUserDisplayName(auth.user)}</h3>
                  </div>
                  <span className={`status-badge ${quickScanResult.action === 'check-in' || quickScanResult.action === 'check-out' || quickScanResult.action === 'completed' ? 'status-success' : quickScanResult.status === 'pending' ? 'status-pending' : 'status-error'}`}>
                    {quickScanResult.action === 'check-in' && 'Checked in ✓'}
                    {quickScanResult.action === 'already-checked-in' && 'Already checked in'}
                    {quickScanResult.action === 'check-out' && 'Checked out ✓'}
                    {quickScanResult.action === 'completed' && 'Completed ✓'}
                    {quickScanResult.action === 'error' && 'Error'}
                  </span>
                </div>
                <p className="attendance-result-detail">{quickScanResult.detail}</p>
                {quickScanResult.action === 'already-checked-in' && activeAttendanceId && (
                  <button
                    type="button"
                    className="checkout-button"
                    onClick={quickCheckout}
                    disabled={attendanceSubmitting || quickLoginLoading}
                  >
                    Check Out
                  </button>
                )}
              </div>
            )}
            {canMarkOwnAttendance && (
              <>
                <div className="scanner-section">
                  <h3>Your personal QR</h3>
                  {auth.user?.qr_token ? (
                    <PersonalQrCode token={auth.user.qr_token} />
                  ) : (
                    <p>No QR token available</p>
                  )}
                </div>

                <div className="actions">
                  <button
                    type="button"
                    onClick={() => markAttendance()}
                    disabled={attendanceSubmitting || quickLoginLoading}
                  >
                    {attendanceSubmitting ? 'Marking...' : 'Mark Attendance'}
                  </button>
                  <button type="button" className="secondary" onClick={checkout}>Check Out</button>
                  <button type="button" className="secondary" onClick={logout}>Logout</button>
                </div>
                {attendanceSuccess && (
                  <div className="attendance-status">
                    <span className="success-indicator">Attendance marked</span>
                  </div>
                )}
              </>
            )}
            {/* Admin hint removed per request */}
            {(isAdmin || isManager) && <button type="button" onClick={exportReport}>Export CSV Report</button>}
          </section>

          {isAdmin && (
            <section className="card admin-action-card register-action-card">
              <details className="admin-action-details" open={showRegisterSection} onToggle={(e) => setShowRegisterSection(e.target.open)}>
                <summary>Register employee/manager</summary>
                <form onSubmit={handleAdminRegister} className="admin-register-form">
                  <input placeholder="Display Name" value={adminForm.display_name} onChange={(e) => setAdminForm({ ...adminForm, display_name: e.target.value })} required />
                  <input type="email" placeholder="Email" value={adminForm.email} onChange={(e) => setAdminForm({ ...adminForm, email: e.target.value })} required />
                  <input type="password" placeholder="Password" value={adminForm.password} onChange={(e) => setAdminForm({ ...adminForm, password: e.target.value })} required />
                  <input placeholder="Username (leave blank for auto-generated)" value={adminForm.username} onChange={(e) => setAdminForm({ ...adminForm, username: e.target.value })} />
                  <input placeholder="Employee/Manager ID (leave blank for auto-generated)" value={adminForm.employee_id} onChange={(e) => setAdminForm({ ...adminForm, employee_id: e.target.value })} />
                  <input placeholder="Department" value={adminForm.department} onChange={(e) => setAdminForm({ ...adminForm, department: e.target.value })} />
                  <input placeholder="Phone" value={adminForm.phone} onChange={(e) => setAdminForm({ ...adminForm, phone: e.target.value })} />
                  <label>
                    Role
                    <select value={adminForm.role} onChange={(e) => setAdminForm({ ...adminForm, role: e.target.value })}>
                      <option value="employee">Employee</option>
                      <option value="manager">Manager</option>
                    </select>
                  </label>
                  <button type="submit" disabled={adminSubmitting}>{adminSubmitting ? 'Creating account...' : 'Create account'}</button>
                </form>
                <p className="hint">Only admins can register employee or manager accounts.</p>
              </details>
            </section>
          )}

          {isAdmin && (
            <section className="card admin-action-card notice-action-card">
              <details className="admin-action-details" open={showNoticeSection} onToggle={(e) => setShowNoticeSection(e.target.open)}>
                <summary>Send notice</summary>
                <form onSubmit={(event) => { event.preventDefault(); submitNotice(); }} className="notice-form">
                  <label>
                    Recipient
                    <select
                      value={noticeForm.recipient}
                      onChange={(e) => setNoticeForm({ ...noticeForm, recipient: e.target.value })}
                      required
                    >
                      <option value="">Select a recipient</option>
                      {dashboard?.employees?.length > 0 && (
                        <optgroup label="Employees">
                          {dashboard.employees.map((user) => (
                            <option key={`employee-${user.user_id}`} value={user.user_id}>
                              {user.display_name || user.username} ({user.role})
                            </option>
                          ))}
                        </optgroup>
                      )}
                      {dashboard?.managers?.length > 0 && (
                        <optgroup label="Managers">
                          {dashboard.managers.map((user) => (
                            <option key={`manager-${user.user_id}`} value={user.user_id}>
                              {user.display_name || user.username} ({user.role})
                            </option>
                          ))}
                        </optgroup>
                      )}
                    </select>
                  </label>
                  <textarea
                    placeholder="Write a message for the recipient"
                    value={noticeForm.message}
                    onChange={(e) => setNoticeForm({ ...noticeForm, message: e.target.value })}
                    required
                  />
                  <button type="submit" disabled={noticeSubmitting}>{noticeSubmitting ? 'Sending notice...' : 'Send notice'}</button>
                </form>
              </details>
            </section>
          )}

          {(isAdmin || isManager || isEmployee) && (
            <section className="card">
              <div className="notice-toggle-row">
                <button type="button" className="toggle-button" onClick={toggleNoticePanel}>
                  {showNoticePanel ? 'Hide notices' : `View notices (${notices?.length || 0})`}
                </button>
                {showNoticePanel && (
                  <button type="button" className="secondary" onClick={() => loadNotices(token)}>
                    Refresh notices
                  </button>
                )}
              </div>
              {showNoticePanel && (
                <div className="notice-dropdown">
                  <h2>{isAdmin ? 'Sent notices' : 'Notices'}</h2>
                  {notices?.length > 0 ? (
                    <div className="notice-list">
                      {notices.map((notice) => (
                        <article className="notice-item" key={notice.id}>
                          <div className="notice-header">
                            <strong>
                              {isAdmin
                                ? `Notice sent to ${notice.recipient_name}`
                                : 'From Admin'}
                            </strong>
                            <span>{formatDateTime(notice.created_at)}</span>
                          </div>
                          <div className="notice-meta">
                            <span>{isAdmin ? `From ${notice.sender_name}` : `To ${notice.recipient_name}`}</span>
                          </div>
                              <p><strong>Notice:</strong> {notice.message}</p>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="hint">No notices yet.</p>
                  )}
                </div>
              )}
            </section>
          )}

          {!isAdmin && attendanceRecordsSection}

        </>
      )}
    </div>
  );
}

export default App;
