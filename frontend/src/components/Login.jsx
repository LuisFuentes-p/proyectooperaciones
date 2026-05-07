import React, { useState } from 'react'

const C = {
  bg: '#0f1117', surface: '#181c27', card: '#1e2333', border: '#2a3045', accent: '#4f8ef7', text: '#e8ecf4', muted: '#6b7896'
};

export default function Login({ onLogin }){
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e){
    e.preventDefault()
    setError(null)
    setLoading(true)
    const result = await onLogin({ username, password })
    setLoading(false)
    if(!result?.ok){
      setError(result?.error || 'Error al iniciar sesión')
    }
  }

  const container = {
    maxWidth: 420, margin: '48px auto', background: C.card, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20, color: C.text,
    boxShadow: '0 8px 30px rgba(2,6,23,0.6)'
  }
  const input = { width: '100%', padding: 10, marginTop: 8, borderRadius: 8, background: C.surface, border: `1px solid ${C.border}`, color: C.text }
  const label = { display: 'block', fontSize: 12, color: C.muted, fontWeight: 700 }
  const btn = { padding: '10px 14px', borderRadius: 8, background: `linear-gradient(180deg, ${C.accent}, ${C.accent}cc)`, color: '#041126', border: 'none', fontWeight: 800, cursor: 'pointer' }

  return (
    <div style={container}>
      <h2 style={{marginTop:0, marginBottom:6}}>Iniciar sesión</h2>
      <div style={{marginBottom:12, color:C.muted, fontSize:13}}>Accede al panel de operaciones</div>
      <form onSubmit={handleSubmit}>
        <div style={{marginBottom:12}}>
          <label style={label}>Usuario</label>
          <input autoFocus value={username} onChange={e=>setUsername(e.target.value)} placeholder="usuario" style={input} />
        </div>

        <div style={{marginBottom:12}}>
          <label style={label}>Contraseña</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="contraseña" style={input} />
        </div>

        {error ? null : null}

        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', gap:12}}>
          <button type="submit" style={btn} disabled={loading}>{loading ? 'Entrando...' : 'Entrar'}</button>
          <div style={{color:C.muted, fontSize:13}}>Credenciales demo: admin / admin</div>
        </div>
      </form>
    </div>
  )
}
