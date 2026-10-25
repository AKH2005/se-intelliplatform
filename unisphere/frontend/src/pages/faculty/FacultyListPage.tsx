import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { facultyApi, departmentsApi, Department, FacultyProfile } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { EmptyState } from '../../components/common/EmptyState';
import { Modal } from '../../components/common/Modal';
import { Breadcrumbs } from '../../components/common/Breadcrumbs';
import { Search, Plus, Filter, Mail, Award, BookOpen, Trash2 } from 'lucide-react';

export const FacultyListPage: React.FC = () => {
  const { user, isAdmin } = useAuth();
  const [facultyList, setFacultyList] = useState<FacultyProfile[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [departmentId, setDepartmentId] = useState('');

  // Add Faculty Modal (Admin only)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newFaculty, setNewFaculty] = useState({
    email: '',
    password: 'Password123!',
    first_name: '',
    last_name: '',
    department_id: '',
    title: 'Assistant Professor',
    office_location: 'Room 301, Engineering Hall',
    bio: ''
  });

  const loadData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [facRes, deptRes] = await Promise.all([
        facultyApi.list({
          search: search || undefined,
          department_id: departmentId ? parseInt(departmentId) : undefined
        }),
        departmentsApi.list()
      ]);
      setFacultyList(facRes.faculty || []);
      setDepartments(deptRes || []);
      if (deptRes.length > 0 && !newFaculty.department_id) {
        setNewFaculty(prev => ({ ...prev, department_id: deptRes[0].id.toString() }));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load faculty directory');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [departmentId]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleCreateFaculty = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      await facultyApi.create({
        email: newFaculty.email,
        password: newFaculty.password,
        first_name: newFaculty.first_name,
        last_name: newFaculty.last_name,
        department_id: parseInt(newFaculty.department_id),
        title: newFaculty.title,
        office_location: newFaculty.office_location,
        bio: newFaculty.bio
      });
      setIsAddModalOpen(false);
      setNewFaculty({
        email: '',
        password: 'Password123!',
        first_name: '',
        last_name: '',
        department_id: departments[0]?.id.toString() || '',
        title: 'Assistant Professor',
        office_location: '',
        bio: ''
      });
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to create faculty member');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (facultyId: number, name: string) => {
    if (!window.confirm(`Are you sure you want to remove faculty member "${name}"?`)) return;
    try {
      await facultyApi.delete(facultyId);
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to remove faculty member');
    }
  };

  return (
    <div className="space-y-6">
      <Breadcrumbs items={[{ label: 'Faculty Directory' }]} />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Faculty Directory</h1>
          <p className="text-sm text-slate-400 mt-1">
            Browse our distinguished professors, instructors, and researchers
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="btn btn-primary self-start md:self-auto"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Faculty Member
          </button>
        )}
      </div>

      {/* Filters Bar */}
      <div className="card p-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-4 items-center">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search faculty by name, title, or bio..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input-field pl-10"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <Filter className="w-4 h-4 text-slate-400 hidden md:block" />
            <select
              value={departmentId}
              onChange={(e) => setDepartmentId(e.target.value)}
              className="input-field"
            >
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>

            <button type="submit" className="btn btn-secondary whitespace-nowrap">
              Search
            </button>
          </div>
        </form>
      </div>

      {/* Faculty Cards Grid */}
      {isLoading ? (
        <LoadingSpinner message="Loading faculty directory..." />
      ) : error ? (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-sm">
          {error}
        </div>
      ) : facultyList.length === 0 ? (
        <EmptyState
          title="No Faculty Found"
          description="Try adjusting your search criteria or department filter."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {facultyList.map((fac) => {
            const fullName = `${fac.user?.first_name} ${fac.user?.last_name}`;
            return (
              <div key={fac.id} className="card p-6 flex flex-col justify-between hover:border-slate-600 transition-colors">
                <div>
                  <div className="flex items-start justify-between">
                    <div className="w-12 h-12 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-lg mb-4">
                      {fac.user?.first_name?.[0]}
                      {fac.user?.last_name?.[0]}
                    </div>
                    {isAdmin && (
                      <button
                        onClick={() => handleDelete(fac.id, fullName)}
                        className="text-slate-400 hover:text-rose-400 p-1"
                        title="Delete Faculty"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  <h3 className="text-lg font-semibold text-white">
                    <Link to={`/faculty/${fac.id}`} className="hover:text-indigo-400 transition-colors">
                      {fullName}
                    </Link>
                  </h3>
                  <p className="text-sm text-indigo-400 font-medium">{fac.title || 'Faculty'}</p>
                  <p className="text-xs text-slate-400 mt-1">{fac.department?.name}</p>

                  <p className="text-sm text-slate-300 mt-3 line-clamp-3">
                    {fac.bio || 'Distinguished academic staff member.'}
                  </p>

                  <div className="mt-4 pt-4 border-t border-slate-700/50 space-y-2 text-xs text-slate-400">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-slate-500" />
                      <span>{fac.user?.email}</span>
                    </div>
                    {fac.office_location && (
                      <div className="flex items-center gap-2">
                        <Award className="w-3.5 h-3.5 text-slate-500" />
                        <span>{fac.office_location}</span>
                      </div>
                    )}
                    {fac.assigned_courses && fac.assigned_courses.length > 0 && (
                      <div className="flex items-center gap-2">
                        <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                        <span className="text-indigo-300 font-medium">
                          {fac.assigned_courses.length} Course{fac.assigned_courses.length > 1 ? 's' : ''} Assigned
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-700/50 flex items-center justify-end">
                  <Link to={`/faculty/${fac.id}`} className="btn btn-secondary text-xs py-1.5 px-3">
                    View Profile & Courses
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Faculty Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Faculty Member"
      >
        <form onSubmit={handleCreateFaculty} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">First Name *</label>
              <input
                type="text"
                required
                value={newFaculty.first_name}
                onChange={(e) => setNewFaculty({ ...newFaculty, first_name: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Last Name *</label>
              <input
                type="text"
                required
                value={newFaculty.last_name}
                onChange={(e) => setNewFaculty({ ...newFaculty, last_name: e.target.value })}
                className="input-field"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Email Address *</label>
            <input
              type="email"
              required
              value={newFaculty.email}
              onChange={(e) => setNewFaculty({ ...newFaculty, email: e.target.value })}
              className="input-field"
              placeholder="prof.name@unisphere.edu"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Department *</label>
            <select
              required
              value={newFaculty.department_id}
              onChange={(e) => setNewFaculty({ ...newFaculty, department_id: e.target.value })}
              className="input-field"
            >
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.code})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Academic Title</label>
              <input
                type="text"
                value={newFaculty.title}
                onChange={(e) => setNewFaculty({ ...newFaculty, title: e.target.value })}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Office Location</label>
              <input
                type="text"
                value={newFaculty.office_location}
                onChange={(e) => setNewFaculty({ ...newFaculty, office_location: e.target.value })}
                className="input-field"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Biography</label>
            <textarea
              rows={3}
              value={newFaculty.bio}
              onChange={(e) => setNewFaculty({ ...newFaculty, bio: e.target.value })}
              className="input-field"
              placeholder="Academic credentials, research areas..."
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
            <button
              type="button"
              onClick={() => setIsAddModalOpen(false)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary"
            >
              {isSubmitting ? 'Creating...' : 'Create Faculty'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
