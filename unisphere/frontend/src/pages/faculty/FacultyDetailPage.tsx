import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { facultyApi, FacultyProfile, Course } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { Breadcrumbs } from '../../components/common/Breadcrumbs';
import { Modal } from '../../components/common/Modal';
import { Mail, Award, BookOpen, Users, Edit3, ArrowLeft } from 'lucide-react';

export const FacultyDetailPage: React.FC = () => {
  const { facultyId } = useParams<{ facultyId: string }>();
  const navigate = useNavigate();
  const { isAdmin } = useAuth();

  const [faculty, setFaculty] = useState<FacultyProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Edit State
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [editForm, setEditForm] = useState({
    title: '',
    office_location: '',
    bio: ''
  });

  const loadFaculty = async () => {
    if (!facultyId) return;
    try {
      setIsLoading(true);
      setError(null);
      const data = await facultyApi.get(parseInt(facultyId));
      setFaculty(data);
      setEditForm({
        title: data.title || '',
        office_location: data.office_location || '',
        bio: data.bio || ''
      });
    } catch (err: any) {
      setError(err.message || 'Faculty member not found');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadFaculty();
  }, [facultyId]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!faculty) return;
    try {
      setIsUpdating(true);
      const updated = await facultyApi.update(faculty.id, editForm);
      setFaculty(updated);
      setIsEditOpen(false);
    } catch (err: any) {
      alert(err.message || 'Failed to update faculty profile');
    } finally {
      setIsUpdating(false);
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading faculty details..." />;
  }

  if (error || !faculty) {
    return (
      <div className="card p-8 text-center max-w-md mx-auto my-12">
        <h2 className="text-xl font-bold text-white mb-2">Faculty Member Not Found</h2>
        <p className="text-sm text-slate-400 mb-6">
          The requested faculty profile could not be located or has been removed.
        </p>
        <Link to="/faculty" className="btn btn-primary inline-flex items-center">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Faculty Directory
        </Link>
      </div>
    );
  }

  const fullName = `${faculty.user?.first_name} ${faculty.user?.last_name}`;

  return (
    <div className="space-y-6">
      <Breadcrumbs
        items={[
          { label: 'Faculty Directory', path: '/faculty' },
          { label: fullName }
        ]}
      />

      {/* Header Profile Card */}
      <div className="card p-6 md:p-8">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <div className="w-20 h-20 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-3xl">
              {faculty.user?.first_name?.[0]}
              {faculty.user?.last_name?.[0]}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-white">{fullName}</h1>
                <span className="badge badge-info">{faculty.title || 'Faculty Member'}</span>
              </div>
              <p className="text-sm text-indigo-400 font-medium mt-1">
                {faculty.department?.name} ({faculty.department?.code})
              </p>
              <div className="flex flex-wrap items-center gap-4 mt-3 text-xs text-slate-400">
                <div className="flex items-center gap-1.5">
                  <Mail className="w-3.5 h-3.5 text-slate-500" />
                  <span>{faculty.user?.email}</span>
                </div>
                {faculty.office_location && (
                  <div className="flex items-center gap-1.5">
                    <Award className="w-3.5 h-3.5 text-slate-500" />
                    <span>Office: {faculty.office_location}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {isAdmin && (
            <button
              onClick={() => setIsEditOpen(true)}
              className="btn btn-secondary self-start md:self-auto"
            >
              <Edit3 className="w-4 h-4 mr-2" />
              Edit Profile
            </button>
          )}
        </div>

        {faculty.bio && (
          <div className="mt-6 pt-6 border-t border-slate-700/50">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Academic Biography
            </h3>
            <p className="text-sm text-slate-300 leading-relaxed">{faculty.bio}</p>
          </div>
        )}
      </div>

      {/* Assigned Courses Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-indigo-400" />
            Assigned Teaching Courses
          </h2>
          <span className="text-xs text-slate-400">
            {faculty.assigned_courses?.length || 0} active courses
          </span>
        </div>

        {(!faculty.assigned_courses || faculty.assigned_courses.length === 0) ? (
          <div className="card p-6 text-center text-sm text-slate-400">
            No active courses assigned to this faculty member for the current semester.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {faculty.assigned_courses.map((course: Course) => (
              <div key={course.id} className="card p-5 flex flex-col justify-between hover:border-slate-600 transition-colors">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="badge badge-info">{course.code}</span>
                    <span className="text-xs text-slate-400">{course.credits} Credits</span>
                  </div>
                  <h3 className="text-base font-semibold text-white mb-2">
                    <Link to={`/courses/${course.id}`} className="hover:text-indigo-400 transition-colors">
                      {course.name}
                    </Link>
                  </h3>
                  <p className="text-xs text-slate-300 line-clamp-2 mb-4">
                    {course.description || 'No description provided.'}
                  </p>
                </div>

                <div className="pt-4 border-t border-slate-700/50 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Users className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{course.enrollment_count || 0} enrolled</span>
                  </div>
                  <Link to={`/courses/${course.id}`} className="text-indigo-400 hover:text-indigo-300 font-medium">
                    Course Details →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edit Modal */}
      <Modal
        isOpen={isEditOpen}
        onClose={() => setIsEditOpen(false)}
        title={`Edit Faculty Profile — ${fullName}`}
      >
        <form onSubmit={handleUpdate} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Academic Title</label>
            <input
              type="text"
              value={editForm.title}
              onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Office Location</label>
            <input
              type="text"
              value={editForm.office_location}
              onChange={(e) => setEditForm({ ...editForm, office_location: e.target.value })}
              className="input-field"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Biography</label>
            <textarea
              rows={4}
              value={editForm.bio}
              onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
              className="input-field"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
            <button
              type="button"
              onClick={() => setIsEditOpen(false)}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUpdating}
              className="btn btn-primary"
            >
              {isUpdating ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
