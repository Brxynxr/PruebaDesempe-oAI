import React, { useState } from 'react';
import { Lock, User, ShieldCheck, AlertCircle, ArrowLeft, LogIn } from 'lucide-react';
import { adminLogin } from '../services/api';
import { useLanguage } from '../context/LanguageContext';

export default function AdminLogin({ onLoginSuccess, onBackToSite }) {
  const { language } = useLanguage();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError(language === 'es' ? 'Ingresa tu usuario y contraseña.' : 'Enter your username and password.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await adminLogin(username.trim(), password);
      onLoginSuccess();
    } catch (err) {
      setError(err.message || (language === 'es' ? 'Credenciales incorrectas.' : 'Invalid credentials.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-wrapper fade-in">
      <div className="admin-login-card glass-panel">
        <div className="admin-login-header">
          <div className="admin-badge-icon">
            <ShieldCheck size={36} className="gold-text" />
          </div>
          <h2 className="admin-title">
            {language === 'es' ? 'Portal de Agentes & Administración' : 'Agent & Admin Portal'}
          </h2>
          <p className="admin-subtitle">
            {language === 'es' 
              ? 'Acceso seguro para asesores de admisiones y gestión académica'
              : 'Secure access for admissions advisors and academic management'}
          </p>
        </div>

        {error && (
          <div className="admin-error-alert slide-up">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="admin-login-form">
          <div className="admin-form-group">
            <label className="admin-label">
              {language === 'es' ? 'Usuario' : 'Username'}
            </label>
            <div className="admin-input-wrapper">
              <User size={18} className="admin-input-icon" />
              <input
                type="text"
                className="admin-input"
                placeholder={language === 'es' ? 'Ej. admin' : 'e.g. admin'}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
                disabled={loading}
              />
            </div>
          </div>

          <div className="admin-form-group">
            <label className="admin-label">
              {language === 'es' ? 'Contraseña' : 'Password'}
            </label>
            <div className="admin-input-wrapper">
              <Lock size={18} className="admin-input-icon" />
              <input
                type="password"
                className="admin-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                disabled={loading}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-admin-submit"
            disabled={loading}
          >
            {loading ? (
              <span>{language === 'es' ? 'Iniciando sesión...' : 'Signing in...'}</span>
            ) : (
              <>
                <LogIn size={18} />
                <span>{language === 'es' ? 'Ingresar al Backoffice' : 'Sign In to Backoffice'}</span>
              </>
            )}
          </button>
        </form>

        <div className="admin-demo-box">
          <span className="demo-box-title">{language === 'es' ? 'Credenciales de Acceso Asesor:' : 'Advisor Credentials:'}</span>
          <div className="demo-credentials-row">
            <span className="demo-cred-tag">Usuario: <code>admin</code></span>
            <span className="demo-cred-tag">Clave: <code>LuminaAdmin2026!</code></span>
          </div>
          <button 
            type="button" 
            className="btn-quick-fill"
            onClick={() => {
              setUsername('admin');
              setPassword('LuminaAdmin2026!');
            }}
          >
            {language === 'es' ? '⚡ Autocompletar credenciales' : '⚡ Auto-fill credentials'}
          </button>
        </div>

        <div className="admin-login-footer">
          <button
            type="button"
            className="btn-back-to-site"
            onClick={onBackToSite}
          >
            <ArrowLeft size={16} />
            <span>{language === 'es' ? 'Volver al Sitio Web' : 'Back to Public Site'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
