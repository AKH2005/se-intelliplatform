import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  Search,
  Filter,
  Plus,
  ArrowRight,
  GraduationCap,
  Trash2,
  Edit2,
} from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { Modal } from '../../components/common/Modal';
import { Toast } from '../../components/common/Toast';

export const StudentsListPage: React.FC = () => {
  const { user, isAdmin } = useAuth();
  const [students, setStudents] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [deptFilter, setDeptFilter] = useState<number | ''>('');
  const [yearFilter, setYearFilter] = useState<number | ''>('');
  const [sortBy, setSortBy] = useState('name');
  const [isLoading, setIsLoading] = useState(true);

  // Add Student modal
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('StudentPass123!');
  const [studentIdNumber, setStudentIdNumber] = useState('');
  const [departmentId, setDepartmentId] = useState<number>(1);
  const [year, setYear] = useState<number>(1);
  const [gpa, setGpa] = useState<number>(3.5);
  const [phone, setPhone] = useState('+1 (555) 019-3321');
  const [address, setAddress] = useState('400 University Quad Dorms');
  const [addError, setAddError] = useState<string | null>(null);

  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fetchStudents = async () => {
    setIsLoading(true);
    try {
      const [sList, dList] = await Promise.all([
        api.students.list({
          search: search || undefined,
          department_id: deptFilter !== '' ? Number(deptFilter) : undefined,
          year: yearFilter !== '' ? Number(yearFilter) : undefined,
          sort_by: sortBy,
        }),
        api.departments.list(),
      ]);
      setStudents(sList);
      setDepartments(dList);
    } catch (err) {
      console.error('Failed to load students:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [search, deptFilter, yearFilter, sortBy]);

  const handleCreateStudent = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddError(null);
    try {
      const created = await api.students.create({
        full_name: name.trim(),
        email: email.trim().toLowerCase(),
        password,
        student_id_number: studentIdNumber.trim().toUpperCase(),
        department_id: Number(departmentId),
        year: Number(year),
        semester: 1,
        gpa: Number(gpa),
        phone: phone.trim(),
        address: address.trim(),
      });
      setIsAddOpen(false);
      setName('');
      setEmail('');
      setStudentIdNumber('');
      setToast({ type: 'success', message: `Student ${created.full_name} added successfully.` });
      fetchStudents();
    } catch (err: any) {
      setAddError(err.message || 'Failed to add student');
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#ffffff', marginBottom: '0.25rem' }}>
            Students Directory
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            Search, filter, inspect academic dossiers, and manage student enrollments.
          </p>
        </div>

        {isAdmin && (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setIsAddOpen(true)}
          >
            <Plus size={16} />
            <span>Add Student</span>
          </button>
        )}
      </div>

      {/* Filter Bar */}
      <div
        className="card"
        style={{
          marginBottom: '1.75rem',
          padding: '1.25rem',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '1rem',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ position: 'relative', flex: '1 1 260px' }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
          <input
            type="text"
            className="form-input"
            placeholder="Search student name, ID number, or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: '2.25rem' }}
          />
        </div>

        <div style={{ flex: '0 1 180px' }}>
          <select
            className="form-select"
            value={deptFilter}
            onChange={(e) => setDeptFilter(e.target.value ? Number(e.target.value) : '')}
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
            ))}
          </select>
        </div>

        <div style={{ flex: '0 1 140px' }}>
          <select
            className="form-select"
            value={yearFilter}
            onChange={(e) => setYearFilter(e.target.value ? Number(e.target.value) : '')}
          >
            <option value="">All Years</option>
            <option value="1">Year 1</option>
            <option value="2">Year 2</option>
            <option value="3">Year 3</option>
            <option value="4">Year 4</option>
          </select>
        </div>

        <div style={{ flex: '0 1 160px' }}>
          <select
            className="form-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="name">Sort by Name</option>
            <option value="gpa">Sort by GPA</option>
            <option value="student_id">Sort by Student ID</option>
          </select>
        </div>
      </div>

      {/* Students Data Table */}
      {isLoading ? (
        <LoadingSpinner label="Loading student directory..." />
      ) : students.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No Students Found"
          description="We could not find any student records matching your search and filter criteria."
          actionLabel="Clear Filters"
          onAction={() => {
            setSearch('');
            setDeptFilter('');
            setYearFilter('');
          }}
        />
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Full Name</th>
                <th>Department</th>
                <th>Class Standing</th>
                <th>GPA</th>
                <th>Contact</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {students.map((st) => (
                <tr key={st.id}>
                  <td>
                    <span className="badge badge-info">{st.student_id_number}</span>
                  </td>
                  <td>
                    {/* Link to Student Detail (Journey A & B) */}
                    <Link
                      to={`/students/${st.id}`}
                      style={{ fontWeight: 700, color: 'var(--accent-primary)' }}
                    >
                      {st.full_name}
                    </Link>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{st.email}</div>
                  </td>
                  <td style={{ color: 'var(--text-muted)' }}>{st.department_name}</td>
                  <td>Year {st.year} • Sem {st.semester}</td>
                  <td>
                    <span style={{ fontWeight: 700, color: st.gpa >= 3.5 ? 'var(--accent-emerald)' : 'var(--text-main)' }}>
                      {st.gpa.toFixed(2)}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{st.phone || 'N/A'}</td>
                  <td>
                    <Link to={`/students/${st.id}`} className="btn btn-outline btn-sm">
                      <span>Dossier</span>
                      <ArrowRight size={13} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Student Modal */}
      <Modal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        title="Register New Student (Admin)"
        footer={
          <>
            <button type="button" className="btn btn-secondary" onClick={() => setIsAddOpen(false)}>
              Cancel
            </button>
            <button type="submit" form="add-student-form" className="btn btn-primary">
              Save Student Record
            </button>
          </>
        }
      >
        <form id="add-student-form" onSubmit={handleCreateStudent}>
          {addError && (
            <div style={{ padding: '0.75rem', background: 'rgba(244, 63, 94, 0.15)', color: '#fda4af', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', marginBottom: '1rem' }}>
              {addError}
            </div>
          )}
          <div className="form-group">
            <label className="form-label">Full Name *</label>
            <input type="text" className="form-input" required value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">University Email *</label>
            <input type="email" className="form-input" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Student ID Number *</label>
              <input type="text" className="form-input" required placeholder="e.g. CS-2026-042" value={studentIdNumber} onChange={(e) => setStudentIdNumber(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Department *</label>
              <select className="form-select" value={departmentId} onChange={(e) => setDepartmentId(Number(e.target.value))}>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
                ))}
              </select>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Academic Year</label>
              <input type="number" className="form-input" min={1} max={4} value={year} onChange={(e) => setYear(Number(e.target.value))} />
            </div>
            <div className="form-group">
              <label className="form-label">Starting GPA</label>
              <input type="number" step="0.01" min={0} max={4.0} className="form-input" value={gpa} onChange={(e) => setGpa(Number(e.target.value))} />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Phone Number</label>
            <input type="text" className="form-input" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Campus Address</label>
            <input type="text" className="form-input" value={address} onChange={(e) => setAddress(e.target.value)} />
          </div>
        </form>
      </Modal>

      {toast && <Toast type={toast.type} message={toast.message} onClose={() => setToast(null)} />}
    </div>
  );
};
