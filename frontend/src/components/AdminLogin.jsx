import React, { useState } from 'react';
import { ArrowLeft, Lock, User, Eye, EyeOff, Loader2, ShieldCheck } from 'lucide-react';
import { adminLogin } from '../services/api';

export default function AdminLogin({ onLoginSuccess, onBackToLanding }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const data = await adminLogin(username.trim(), password);
      onLoginSuccess(data);
    } catch (err) {
      setError(err.message || 'Credenciales incorrectas. Verifica tu usuario y contraseña.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full bg-cream font-sans text-ink antialiased selection:bg-brand/30">
      {/* Warm gradient background */}
      <div className="pointer-events-none fixed inset-0 -z-10">
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(135deg, #FFF6EC 0%, #FCE3D2 38%, #F7D2CB 66%, #EAD7E8 100%)",
          }}
        />
        <div className="absolute -top-40 -right-28 h-[560px] w-[560px] rounded-full bg-gold/40 blur-3xl" />
        <div className="absolute -bottom-52 -left-40 h-[520px] w-[520px] rounded-full bg-accent-rose/25 blur-3xl" />
      </div>

      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <button
          onClick={onBackToLanding}
          className="flex items-center gap-2.5 transition hover:opacity-80"
        >
          <div className="grid size-9 place-items-center rounded-2xl bg-white/60 ring-1 ring-black/5 backdrop-blur-sm font-display">
            <span className="text-brand font-bold">L</span>
          </div>
          <span className="text-sm font-semibold tracking-tight font-display text-ink">Academia Lumina</span>
        </button>
      </div>

      <main className="mx-auto flex max-w-md flex-col justify-center px-6 py-10 animate-rise">
        <button
          onClick={onBackToLanding}
          className="mb-6 inline-flex w-fit items-center gap-1.5 rounded-full bg-white/60 px-3.5 py-1.5 text-xs font-medium ring-1 ring-black/5 transition hover:bg-white/90"
        >
          <ArrowLeft size={14} />
          Volver al sitio web
        </button>

        <div className="rounded-3xl bg-white/50 p-8 ring-1 ring-black/5 backdrop-blur-md shadow-lg">
          <div className="mb-6">
            <div className="text-xs uppercase tracking-[0.2em] text-ink/50 font-semibold">Acceso Asesores</div>
            <h1 className="mt-2 text-3xl font-light font-display text-ink">Portal del Asesor</h1>
            <p className="mt-1 text-sm text-ink/65 leading-relaxed">
              Ingresa tus credenciales para gestionar solicitudes de admisión y chats en vivo.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-ink/75">Usuario</label>
              <div className="relative">
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full rounded-2xl bg-white/80 px-4 py-3 text-sm text-ink outline-none ring-1 ring-black/10 transition focus:ring-2 focus:ring-ink"
                  placeholder="admin / tu_usuario"
                  required
                />
              </div>
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-medium text-ink/75">Contraseña</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-2xl bg-white/80 px-4 py-3 pr-10 text-sm text-ink outline-none ring-1 ring-black/10 transition focus:ring-2 focus:ring-ink"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-ink/40 transition hover:text-ink"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="rounded-2xl bg-rose/50 px-4 py-3 text-xs text-ink ring-1 ring-rose/60 leading-relaxed">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="flex w-full items-center justify-center gap-2 rounded-2xl bg-ink py-3.5 text-sm font-medium text-cream shadow-md transition hover:bg-ink/90 active:scale-98 disabled:opacity-60"
            >
              {isLoading && <Loader2 size={16} className="animate-spin" />}
              <span>{isLoading ? 'Autenticando...' : 'Ingresar al panel'}</span>
            </button>
          </form>

          <div className="mt-8 border-t border-black/5 pt-4 text-center text-xs text-ink/50 flex items-center justify-center gap-1.5">
            <ShieldCheck size={14} className="text-brand" />
            <span>Sistema Seguro de Atención Lumina</span>
          </div>
        </div>
      </main>
    </div>
  );
}
