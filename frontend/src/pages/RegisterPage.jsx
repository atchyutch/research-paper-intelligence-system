import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import toast from 'react-hot-toast';
import { BookOpen, ArrowRight, Eye, EyeOff } from 'lucide-react';

export default function RegisterPage() {
  const [form, setForm] = useState({ firstName: '', lastName: '', email: '', password: '' });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const { firstName, lastName, email, password } = form;
    if (!firstName.trim() || !lastName.trim() || !email.trim() || !password.trim()) {
      toast.error('All fields are required');
      return;
    }
    setLoading(true);
    try {
      await register(firstName, lastName, email, password);
      toast.success('Account created!');
      navigate('/');
    } catch (err) {
      toast.error(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  }

  const inputClass = `w-full px-4 py-2.5 rounded-lg border border-paper-300 bg-paper-50 text-ink-900 text-sm
    placeholder:text-ink-400 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent
    transition-all duration-200`;

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper-100 px-4">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-accent/5 blur-3xl" />
        <div className="absolute -bottom-48 -right-48 w-[500px] h-[500px] rounded-full bg-ink-200/30 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md animate-fade-in">
        <div className="flex items-center gap-3 mb-10 justify-center">
          <div className="w-11 h-11 rounded-xl bg-ink-950 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-paper-50" strokeWidth={1.8} />
          </div>
          <span className="font-display text-2xl font-semibold tracking-tight text-ink-950">
            Research Paper Intelligence System
          </span>
        </div>

        <div className="bg-white rounded-2xl shadow-[0_2px_24px_-4px_rgba(0,0,0,0.08)] border border-paper-300/60 p-8">
          <h1 className="font-display text-2xl font-semibold text-ink-900 mb-1">
            Create account
          </h1>
          <p className="text-ink-500 text-sm mb-7">
            Start analyzing your research papers
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-ink-600 mb-1.5 uppercase tracking-wider">
                  First name
                </label>
                <input type="text" value={form.firstName} onChange={update('firstName')}
                  className={inputClass} placeholder="Jane" />
              </div>
              <div>
                <label className="block text-xs font-medium text-ink-600 mb-1.5 uppercase tracking-wider">
                  Last name
                </label>
                <input type="text" value={form.lastName} onChange={update('lastName')}
                  className={inputClass} placeholder="Doe" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1.5 uppercase tracking-wider">
                Email
              </label>
              <input type="email" value={form.email} onChange={update('email')}
                className={inputClass} placeholder="you@university.edu" />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={form.password}
                  onChange={update('password')}
                  className={`${inputClass} pr-10`}
                  placeholder="••••••••"
                />
                <button type="button" onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-400 hover:text-ink-600 transition-colors">
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading}
              className="w-full py-2.5 rounded-lg bg-ink-950 text-paper-50 text-sm font-medium
                hover:bg-ink-800 active:scale-[0.98] transition-all duration-150
                disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-2">
              {loading ? (
                <div className="w-4 h-4 border-2 border-paper-300 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>Create account <ArrowRight size={15} /></>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-ink-500 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-accent font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
