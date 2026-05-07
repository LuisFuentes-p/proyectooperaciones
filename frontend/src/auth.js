const AUTH_URL = import.meta.env.VITE_AUTH_URL || 'http://localhost:8004'

function store(data){
  try{ localStorage.setItem('auth_user', JSON.stringify(data)) }catch(e){}
}

export function getStoredUser(){
  try{
    const s = localStorage.getItem('auth_user')
    return s ? JSON.parse(s) : null
  }catch(e){ return null }
}

export async function login({ username, password }){
  // try backend first
  try{
    const res = await fetch(`${AUTH_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })

    if(res.ok){
      const data = await res.json()
      // expect { token, user: { name, role } }
      store(data.user || { name: username, role: data.role || 'admin' })
      return { user: data.user || { name: username, role: data.role || 'admin' } }
    }
  }catch(e){
    // ignore and fallback to local mock
  }

  // fallback mock credentials for development
  if(username === 'admin' && password === 'admin'){
    const user = { name: 'Admin (local)', role: 'admin' }
    store(user)
    return { user }
  }

  return { error: 'Credenciales inválidas' }
}

export function logout(){
  try{ localStorage.removeItem('auth_user') }catch(e){}
}

export default { login, logout, getStoredUser }
