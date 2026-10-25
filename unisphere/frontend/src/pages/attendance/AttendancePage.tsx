import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { attendanceApi, coursesApi, Course, AttendanceSheet, AttendanceStatus } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Breadcrumbs } from '../../components/common/Breadcrumbs';
import { Calendar, CheckCircle2, XCircle, Clock, Save, UserCheck, AlertCircle } from 'lucide-react';

export const AttendancePage: React.FC = () => {
  const { user, isStudent, isFaculty, isAdmin } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string>(searchParams.get('courseId') || '');
  const [selectedDate, setSelectedDate] = useState<string>(
    searchParams.get('date') || new Date().toISOString().split('T')[0]
  );

  const [sheet, setSheet] = useState<AttendanceSheet | null>(null);
  const [studentStatuses, setStudentStatuses] = useState<{ [studentId: number]: AttendanceStatus }>({});
  const [studentRemarks, setStudentRemarks] = useState<{ [studentId: number]: string }>({});

  // Student view
  const [studentSummary, setStudentSummary] = useState<any | null>(null);

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load courses
  useEffect(() => {
    const loadCourses = async () => {
      try {
        const res = await coursesApi.list();
        setCourses(res.courses || []);
        if (res.courses.length > 0 && !selectedCourseId) {
          setSelectedCourseId(res.courses[0].id.toString());
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load courses');
      }
    };
    loadCourses();
  }, []);

  // Load roster or student view
  useEffect(() => {
    if (isStudent && user?.profile_id) {
      loadStudentAttendance(user.profile_id);
    } else if (selectedCourseId && selectedDate) {
      loadCourseSheet(parseInt(selectedCourseId), selectedDate);
    }
  }, [selectedCourseId, selectedDate, isStudent, user]);

  const loadStudentAttendance = async (studentId: number) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await attendanceApi.getStudentAttendance(studentId);
      setStudentSummary(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load student attendance');
    } finally {
      setIsLoading(false);
    }
  };

  const loadCourseSheet = async (courseId: number, date: string) => {
    try {
      setIsLoading(true);
      setError(null);
      setSaveSuccess(null);
      const data = await attendanceApi.getCourseSheet(courseId, date);
      setSheet(data);

      // Pre-fill statuses
      const statuses: { [studentId: number]: AttendanceStatus } = {};
      const remarks: { [studentId: number]: string } = {};
      data.students.forEach((s) => {
        statuses[s.student_id] = s.status || AttendanceStatus.PRESENT;
        remarks[s.student_id] = s.remarks || '';
      });
      setStudentStatuses(statuses);
      setStudentRemarks(remarks);
    } catch (err: any) {
      setError(err.message || 'Failed to load attendance sheet');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusChange = (studentId: number, status: AttendanceStatus) => {
    setStudentStatuses((prev) => ({ ...prev, [studentId]: status }));
  };

  const handleRemarkChange = (studentId: number, remark: string) => {
    setStudentRemarks((prev) => ({ ...prev, [studentId]: remark }));
  };

  const handleMarkAll = (status: AttendanceStatus) => {
    if (!sheet) return;
    const updated: { [studentId: number]: AttendanceStatus } = {};
    sheet.students.forEach((s) => {
      updated[s.student_id] = status;
    });
    setStudentStatuses(updated);
  };

  const handleSaveAttendance = async () => {
    if (!selectedCourseId || !selectedDate || !sheet) return;
    try {
      setIsSaving(true);
      setError(null);
      setSaveSuccess(null);

      const records = sheet.students.map((s) => ({
        student_id: s.student_id,
        status: studentStatuses[s.student_id] || AttendanceStatus.PRESENT,
        remarks: studentRemarks[s.student_id] || undefined
      }));

      await attendanceApi.saveBatch(parseInt(selectedCourseId), selectedDate, records);
      setSaveSuccess('Attendance saved successfully and persisted to database!');

      // Re-fetch sheet to verify persistence
      await loadCourseSheet(parseInt(selectedCourseId), selectedDate);
    } catch (err: any) {
      setError(err.message || 'Failed to save attendance');
    } finally {
      setIsSaving(false);
    }
  };

  // Compute live statistics
  const totalRoster = sheet?.students.length || 0;
  const presentCount = Object.values(studentStatuses).filter((s) => s === AttendanceStatus.PRESENT).length;
  const absentCount = Object.values(studentStatuses).filter((s) => s === AttendanceStatus.ABSENT).length;
  const lateCount = Object.values(studentStatuses).filter((s) => s === AttendanceStatus.LATE).length;
  const attendancePercentage = totalRoster > 0 ? Math.round(((presentCount + lateCount * 0.5) / totalRoster) * 100) : 0;

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Attendance Management' }]} />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Attendance Management</h1>
          <p className="text-sm text-slate-400 mt-1">
            {isStudent
              ? 'View your personal attendance history and compliance statistics'
              : 'Record, update, and manage student course attendance rosters'}
          </p>
        </div>

        {!isStudent && sheet && sheet.students.length > 0 && (
          <button
            onClick={handleSaveAttendance}
            disabled={isSaving}
            className="btn btn-primary self-start md:self-auto flex items-center"
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? 'Saving...' : 'Save Attendance'}
          </button>
        )}
      </div>

      {saveSuccess && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg text-sm flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{saveSuccess}</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* STUDENT VIEW */}
      {isStudent && (
        <div className="space-y-6">
          {isLoading ? (
            <LoadingSpinner message="Loading attendance records..." />
          ) : studentSummary ? (
            <>
              {/* Summary Stats */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="card p-5">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Attendance Rate</div>
                  <div className="text-3xl font-bold text-white mt-2">
                    {studentSummary.overall_percentage}%
                  </div>
                  <div className="text-xs text-slate-400 mt-1">Total recorded sessions</div>
                </div>
                <div className="card p-5">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Present Sessions</div>
                  <div className="text-3xl font-bold text-emerald-400 mt-2">
                    {studentSummary.present_count}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">Sessions attended on time</div>
                </div>
                <div className="card p-5">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Late Sessions</div>
                  <div className="text-3xl font-bold text-amber-400 mt-2">
                    {studentSummary.late_count}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">Partial credit sessions</div>
                </div>
                <div className="card p-5">
                  <div className="text-xs text-slate-400 uppercase font-semibold">Absences</div>
                  <div className="text-3xl font-bold text-rose-400 mt-2">
                    {studentSummary.absent_count}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">Missed lecture sessions</div>
                </div>
              </div>

              {/* Attendance Table */}
              <div className="card p-6">
                <h3 className="text-base font-semibold text-white mb-4">Detailed Attendance Log</h3>
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Course</th>
                        <th>Status</th>
                        <th>Remarks</th>
                      </tr>
                    </thead>
                    <tbody>
                      {studentSummary.records?.map((rec: any) => (
                        <tr key={rec.id}>
                          <td className="font-mono text-xs">{rec.date}</td>
                          <td className="font-medium text-white">{rec.course?.name || `Course #${rec.course_id}`}</td>
                          <td>
                            <span
                              className={`badge ${
                                rec.status === AttendanceStatus.PRESENT
                                  ? 'badge-success'
                                  : rec.status === AttendanceStatus.LATE
                                  ? 'badge-warning'
                                  : 'badge-danger'
                              }`}
                            >
                              {rec.status}
                            </span>
                          </td>
                          <td className="text-slate-400 text-xs">{rec.remarks || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="card p-6 text-center text-slate-400">
              No attendance records found for your account.
            </div>
          )}
        </div>
      )}

      {/* FACULTY & ADMIN VIEW */}
      {!isStudent && (
        <div className="space-y-6">
          {/* Controls Bar */}
          <div className="card p-5">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Select Course *
                </label>
                <select
                  value={selectedCourseId}
                  onChange={(e) => {
                    setSelectedCourseId(e.target.value);
                    setSearchParams({ courseId: e.target.value, date: selectedDate });
                  }}
                  className="input-field"
                >
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.code} — {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Lecture Date *
                </label>
                <div className="relative">
                  <input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => {
                      setSelectedDate(e.target.value);
                      setSearchParams({ courseId: selectedCourseId, date: e.target.value });
                    }}
                    className="input-field"
                  />
                </div>
              </div>

              <div className="flex flex-col justify-end">
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => handleMarkAll(AttendanceStatus.PRESENT)}
                    className="btn btn-secondary text-xs flex-1"
                  >
                    Mark All Present
                  </button>
                  <button
                    type="button"
                    onClick={() => handleMarkAll(AttendanceStatus.ABSENT)}
                    className="btn btn-secondary text-xs flex-1"
                  >
                    Mark All Absent
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Real-time stats card */}
          {sheet && sheet.students.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="card p-4 text-center">
                <span className="text-xs text-slate-400">Enrolled Students</span>
                <p className="text-2xl font-bold text-white mt-1">{totalRoster}</p>
              </div>
              <div className="card p-4 text-center">
                <span className="text-xs text-slate-400">Present</span>
                <p className="text-2xl font-bold text-emerald-400 mt-1">{presentCount}</p>
              </div>
              <div className="card p-4 text-center">
                <span className="text-xs text-slate-400">Late</span>
                <p className="text-2xl font-bold text-amber-400 mt-1">{lateCount}</p>
              </div>
              <div className="card p-4 text-center">
                <span className="text-xs text-slate-400">Attendance Rate</span>
                <p className="text-2xl font-bold text-indigo-400 mt-1">{attendancePercentage}%</p>
              </div>
            </div>
          )}

          {/* Roster Sheet */}
          {isLoading ? (
            <LoadingSpinner message="Loading course attendance sheet..." />
          ) : !sheet || sheet.students.length === 0 ? (
            <div className="card p-8 text-center text-slate-400">
              <UserCheck className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <h3 className="text-base font-semibold text-white">No Students Enrolled</h3>
              <p className="text-xs mt-1">There are no students currently enrolled in this course.</p>
            </div>
          ) : (
            <div className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-white">
                  Student Roster ({sheet.students.length}) — {selectedDate}
                </h3>
                <span className="text-xs text-slate-400">
                  Click status pill to toggle Present / Late / Absent
                </span>
              </div>

              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Student Number</th>
                      <th>Student Name</th>
                      <th>Attendance Status</th>
                      <th>Remarks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sheet.students.map((student) => {
                      const currentStatus = studentStatuses[student.student_id] || AttendanceStatus.PRESENT;
                      return (
                        <tr key={student.student_id}>
                          <td className="font-mono text-xs font-semibold text-slate-300">
                            {student.student_number}
                          </td>
                          <td className="font-medium text-white">{student.student_name}</td>
                          <td>
                            <div className="flex items-center gap-1.5">
                              <button
                                type="button"
                                onClick={() => handleStatusChange(student.student_id, AttendanceStatus.PRESENT)}
                                className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
                                  currentStatus === AttendanceStatus.PRESENT
                                    ? 'bg-emerald-600 text-white shadow-sm'
                                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                                }`}
                              >
                                Present
                              </button>
                              <button
                                type="button"
                                onClick={() => handleStatusChange(student.student_id, AttendanceStatus.LATE)}
                                className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
                                  currentStatus === AttendanceStatus.LATE
                                    ? 'bg-amber-600 text-white shadow-sm'
                                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                                }`}
                              >
                                Late
                              </button>
                              <button
                                type="button"
                                onClick={() => handleStatusChange(student.student_id, AttendanceStatus.ABSENT)}
                                className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
                                  currentStatus === AttendanceStatus.ABSENT
                                    ? 'bg-rose-600 text-white shadow-sm'
                                    : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                                }`}
                              >
                                Absent
                              </button>
                            </div>
                          </td>
                          <td>
                            <input
                              type="text"
                              placeholder="Add optional notes..."
                              value={studentRemarks[student.student_id] || ''}
                              onChange={(e) => handleRemarkChange(student.student_id, e.target.value)}
                              className="input-field text-xs py-1"
                            />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  type="button"
                  onClick={handleSaveAttendance}
                  disabled={isSaving}
                  className="btn btn-primary"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {isSaving ? 'Saving...' : 'Save & Persist Attendance'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
