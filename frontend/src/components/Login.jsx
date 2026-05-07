import React, { useState } from 'react'

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
    if(!result.ok){
      setError(result.error || 'Error al iniciar sesión')
    }
  }

  return (
    <div className="module" style={{maxWidth:420, margin:'40px auto'}}>
      <h2 style={{marginTop:0}}>Iniciar sesión</h2>
      <form onSubmit={handleSubmit}>
        <div style={{marginBottom:10}}>
          <label>Usuario</label>
          <input autoFocus value={username} onChange={e=>setUsername(e.target.value)} placeholder="usuario" style={{width:'100%', padding:8, marginTop:6}} />
        </div>

        <div style={{marginBottom:10}}>
          <label>Contraseña</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="contraseña" style={{width:'100%', padding:8, marginTop:6}} />
        </div>

        {error && <div style={{color:'crimson', marginBottom:10}}>{error}</div>}

        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
          <button type="submit" style={{padding:'8px 12px'}} disabled={loading}>{loading ? 'Entrando...' : 'Entrar'}</button>
          <div style={{color:'#6b7280', fontSize:13}}>Credenciales demo: admin / admin</div>
        </div>
      </form>
    </div>
  )
}
