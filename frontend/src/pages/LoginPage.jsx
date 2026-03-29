import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import toast from 'react-hot-toast';
import { BookOpen, ArrowRight, Eye, EyeOff } from 'lucide-react';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      toast.error('Please fill in all fields');
      return;
    }
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back');
      navigate('/');
    } catch (err) {
      toast.error(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-paper-100 px-4">
      {/* Decorative background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-accent/5 blur-3xl" />
        <div className="absolute -bottom-48 -left-48 w-[500px] h-[500px] rounded-full bg-ink-200/30 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-10 justify-center">
          <div className="w-11 h-11 rounded-xl bg-ink-950 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-paper-50" strokeWidth={1.8} />
          </div>
          <span className="font-display text-2xl font-semibold tracking-tight text-ink-950">
            Research Paper Intelligence System
          </span>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-[0_2px_24px_-4px_rgba(0,0,0,0.08)] border border-paper-300/60 p-8">
          <h1 className="font-display text-2xl font-semibold text-ink-900 mb-1">
            Sign in
          </h1>
          <p className="text-ink-500 text-sm mb-7">
            Access your research conversations
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1.5 uppercase tracking-wider">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg border border-paper-300 bg-paper-50 text-ink-900 text-sm
                  placeholder:text-ink-400 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent
                  transition-all duration-200"
                placeholder="you@university.edu"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-ink-600 mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg border border-paper-300 bg-paper-50 text-ink-900 text-sm
                    placeholder:text-ink-400 focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent
                    transition-all duration-200 pr-10"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-400 hover:text-ink-600 transition-colors"
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-ink-950 text-paper-50 text-sm font-medium
                hover:bg-ink-800 active:scale-[0.98] transition-all duration-150
                disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-paper-300 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  Continue
                  <ArrowRight size={15} />
                </>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-ink-500 mt-6">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="text-accent font-medium hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
