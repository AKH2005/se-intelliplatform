import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, BookOpen, Users, Calendar, ArrowRight, Plus } from 'lucide-react';
import { api } from '../../services/api';
import { Navbar } from '../../components/layout/Navbar';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { useAuth } from '../../context/AuthContext';
import { Modal } from '../../components/common/Modal';

export const CoursesPage: React.FC = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState<number | ''>('');
  const [selectedSemester, setSelectedSemester] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Admin / Faculty course creation
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [code, setCode] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [credits, setCredits] = useState(3);
  const [deptId, setDeptId] = useState<number>(1);
  const [schedule, setSchedule] = useState('Mon/Wed 10:00 - 11:30 AM');
  const [createError, setCreateError] = useState<string | null>(null);

  const fetchCourses = async () => {
    setIsLoading(true);
    try {
      const [cList, dList] = await Promise.all([
        api.courses.list({
          search: search || undefined,
          department_id: selectedDept !== '' ? Number(selectedDept) : undefined,
          semester: selectedSemester || undefined,
        }),
        api.departments.list(),
      ]);
      setCourses(cList);
      setDepartments(dList);
    } catch (err) {
      console.error('Failed to load courses:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, [search, selectedDept, selectedSemester]);

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    try {
      await api.courses.create({
        code: code.trim(),
        title: title.trim(),
        description: description.trim(),
        credits: Number(credits),
        department_id: Number(deptId),
        schedule: schedule.trim(),
      });
      setIsCreateOpen(false);
      setCode('');
      setTitle('');
      setDescription('');
      fetchCourses();
    } catch (err: any) {
      setCreateError(err.message || 'Failed to create course');
    }
  };

  const isStaff = user && (user.role === 'ADMINISTRATOR' || user.role === 'FACULTY');

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />

      <section style={{ padding: '3rem 0 2rem 0', background: 'radial-gradient(ellipse 60% 50% at 50% 0%, rgba(56, 189, 248, 0.08), transparent)', borderBottom: '1px solid var(--border-subtle)' }}>
        <div className="container">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <span className="badge badge-info" style={{ marginBottom: '0.5rem' }}>Course Directory</span>
              <h1 style={{ fontSize: '2.4rem', fontWeight: 800, color: '#ffffff' }}>University Course Catalogue</h1>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                Explore official degree requirements, lecture schedules, and syllabus contracts.
              </p>
            </div>
            {isStaff && (
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setIsCreateOpen(true)}
              >
                <Plus size={16} />
                <span>Add New Course</span>
              </button>
            )}
          </div>
        </div>
      </section>

      <div className="container" style={{ padding: '2.5rem 1.5rem', flex: 1 }}>
        {/* Filters & Search Toolbar */}
        <div
          className="card"
          style={{
            marginBottom: '2rem',
            padding: '1.25rem',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '1rem',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {/* Search Box */}
          <div style={{ position: 'relative', flex: '1 1 280px' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
            <input
              type="text"
              className="form-input"
              placeholder="Search by course name or code (e.g. CS101, Algorithms)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '2.25rem' }}
            />
          </div>

          {/* Department Filter */}
          <div style={{ flex: '0 1 200px' }}>
            <select
              className="form-select"
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value ? Number(e.target.value) : '')}
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>

          {/* Semester Filter */}
          <div style={{ flex: '0 1 180px' }}>
            <select
              className="form-select"
              value={selectedSemester}
              onChange={(e) => setSelectedSemester(e.target.value)}
            >
              <option value="">All Semesters</option>
              <option value="Fall 2026">Fall 2026</option>
              <option value="Spring 2027">Spring 2027</option>
            </select>
          </div>
        </div>

        {/* Course Cards Grid */}
        {isLoading ? (
          <LoadingSpinner label="Querying courses database..." />
        ) : courses.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No Courses Found"
            description="We could not find any courses matching your search criteria. Try modifying your filters or clear the search field."
            actionLabel="Reset Filters"
            onAction={() => {
              setSearch('');
              setSelectedDept('');
              setSelectedSemester('');
            }}
          />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1.5rem' }}>
            {courses.map((course) => (
              <div
                key={course.id}
                className="card card-hover"
                style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.85rem' }}>
                    <span className="badge badge-info">{course.code}</span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontWeight: 600 }}>{course.credits} Credits</span>
                  </div>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#ffffff', marginBottom: '0.5rem' }}>
                    {course.title}
                  </h3>
                  <div style={{ fontSize: '0.78rem', color: 'var(--accent-primary)', marginBottom: '0.85rem', fontWeight: 600 }}>
                    {course.department_name}
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '1.25rem' }}>
                    {course.description || 'Comprehensive curriculum covering foundational principles and applied technical methodologies.'}
                  </p>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-dim)', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem', marginBottom: '1rem' }}>
                    <span>Instructor: <strong style={{ color: 'var(--text-main)' }}>{course.instructor_name}</strong></span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Users size={13} /> {course.enrolled_count}/{course.max_capacity}
                    </span>
                  </div>
                  <Link to={`/courses/${course.id}`} className="btn btn-outline" style={{ width: '100%' }}>
                    <span>Course Details & Syllabus</span>
                    <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Course Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New University Course"
        footer={
          <>
            <button type="button" className="btn btn-secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </button>
            <button type="submit" form="create-course-form" className="btn btn-primary">
              Create Course
            </button>
          </>
        }
      >
        <form id="create-course-form" onSubmit={handleCreateCourse}>
          {createError && (
            <div style={{ padding: '0.75rem', background: 'rgba(244, 63, 94, 0.15)', color: '#fda4af', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', marginBottom: '1rem' }}>
              {createError}
            </div>
          )}
          <div className="form-group">
            <label className="form-label">Course Code (e.g. CS401)</label>
            <input type="text" className="form-input" required value={code} onChange={(e) => setCode(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Course Title</label>
            <input type="text" className="form-input" required value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Department</label>
            <select className="form-select" value={deptId} onChange={(e) => setDeptId(Number(e.target.value))}>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Course Description</label>
            <textarea className="form-textarea" required value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Credits</label>
              <input type="number" className="form-input" min={1} max={6} value={credits} onChange={(e) => setCredits(Number(e.target.value))} />
            </div>
            <div className="form-group">
              <label className="form-label">Lecture Schedule</label>
              <input type="text" className="form-input" value={schedule} onChange={(e) => setSchedule(e.target.value)} />
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
};
