import React, { useEffect, useState } from 'react'
import * as api from '../api/inventario'

function SmallModal({ title, children, onClose }){
  return (
    <div style={{position:'fixed', inset:0, background:'rgba(0,0,0,0.3)', display:'flex', alignItems:'center', justifyContent:'center'}} onClick={onClose}>
      <div style={{width:520, background:'#fff', padding:16, borderRadius:8}} onClick={e=>e.stopPropagation()}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8}}>
          <strong>{title}</strong>
          <button onClick={onClose}>✕</button>
        </div>
        <div>{children}</div>
      </div>
    </div>
  )
}

export default function Inventory({ role, permissions }){
  const canEdit = permissions?.canEdit
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showNew, setShowNew] = useState(false)
  const [active, setActive] = useState(null) // selected product
  const [showEntry, setShowEntry] = useState(false)
  const [showExit, setShowExit] = useState(false)
  const [showTransfer, setShowTransfer] = useState(false)
  const [showAdjust, setShowAdjust] = useState(false)
  const [history, setHistory] = useState([])

  async function load(){
    setLoading(true); setError(null)
    try{
      const res = await api.listProducts()
      setProducts(Array.isArray(res) ? res : (res.products || []))
    }catch(e){
      // fallback mock data
      setError('No se pudo conectar al servicio de inventario, usando datos mock.')
      setProducts([{ sku:'PRD-001', name:'Producto demo', stock:12, id:1 }, { sku:'PRD-002', name:'Otro producto', stock:5, id:2 }])
    }finally{ setLoading(false) }
  }

  useEffect(()=>{ load() }, [])

  async function handleCreate(data){
    try{
      if(!canEdit) throw new Error('Sin permisos')
      await api.createProduct(data)
      setShowNew(false)
      await load()
    }catch(e){ alert('Error creando producto: '+e.message) }
  }

  async function handleDelete(p){
    if(!canEdit) return alert('Sin permisos')
    if(!confirm(`Eliminar ${p.name}?`)) return
    try{ await api.deleteProduct(p.id); await load() }catch(e){ alert('Error: '+e.message) }
  }

  async function openHistory(p){
    setActive(p)
    try{
      const res = await api.getHistory(p.id)
      setHistory(Array.isArray(res) ? res : (res.history || []))
    }catch(e){
      setHistory([{ type:'MOCK', qty:0, note:'Historial no disponible (mock)' }])
    }
  }

  async function handleEntry(qty, warehouse){
    if(!canEdit) return alert('Sin permisos')
    try{ await api.stockEntry(active.id, qty, { warehouse }); setShowEntry(false); await load() }catch(e){ alert('Error: '+e.message) }
  }

  async function handleExit(qty, warehouse){
    if(!canEdit) return alert('Sin permisos')
    try{ await api.stockExit(active.id, qty, { warehouse }); setShowExit(false); await load() }catch(e){ alert('Error: '+e.message) }
  }

  async function handleTransfer(from, to, sku, qty){
    if(!canEdit) return alert('Sin permisos')
    try{ await api.transferStock(from, to, sku, qty); setShowTransfer(false); await load() }catch(e){ alert('Error: '+e.message) }
  }

  async function handleAdjust(qty, reason){
    if(!canEdit) return alert('Sin permisos')
    try{ await api.adjustStock(active.id, qty, reason); setShowAdjust(false); await load() }catch(e){ alert('Error: '+e.message) }
  }

  return (
    <section className="module">
      <div className="module-header">
        <h2>Inventario</h2>
        <div className="module-actions">
          <button onClick={()=>setShowNew(true)} disabled={!canEdit}>Nuevo producto</button>
          <button onClick={()=>{ navigator.clipboard?.writeText(JSON.stringify(products)); alert('Copiado (mock)') }}>Exportar CSV</button>
        </div>
      </div>

      <div className="kpis">
        <div className="kpi">Productos: <strong>{products.length}</strong></div>
        <div className="kpi">Stock total: <strong>{products.reduce((s,p)=>s+(p.stock||0),0)}</strong></div>
      </div>

      {loading && <div>Loading...</div>}
      {error && <div style={{color:'crimson', marginBottom:8}}>{error}</div>}

      <table className="list">
        <thead><tr><th>SKU</th><th>Nombre</th><th>Stock</th><th>Acciones</th></tr></thead>
        <tbody>
          {products.map(p => (
            <tr key={p.id || p.sku}>
              <td>{p.sku}</td>
              <td>{p.name}</td>
              <td>{p.stock ?? '-'}</td>
              <td>
                <button onClick={()=>{ setActive(p); setShowEntry(true) }} disabled={!canEdit}>Entrada</button>
                <button onClick={()=>{ setActive(p); setShowExit(true) }} disabled={!canEdit}>Salida</button>
                <button onClick={()=>openHistory(p)}>Historial</button>
                <button onClick={()=>handleDelete(p)} disabled={!canEdit}>Eliminar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {showNew && (
        <SmallModal title="Nuevo producto" onClose={()=>setShowNew(false)}>
          <ProductForm onSubmit={handleCreate} onCancel={()=>setShowNew(false)} />
        </SmallModal>
      )}

      {showEntry && active && (
        <SmallModal title={`Entrada de stock - ${active.name}`} onClose={()=>setShowEntry(false)}>
          <StockForm onSubmit={(qty,warehouse)=>handleEntry(qty,warehouse)} onCancel={()=>setShowEntry(false)} />
        </SmallModal>
      )}

      {showExit && active && (
        <SmallModal title={`Salida de stock - ${active.name}`} onClose={()=>setShowExit(false)}>
          <StockForm onSubmit={(qty,warehouse)=>handleExit(qty,warehouse)} onCancel={()=>setShowExit(false)} />
        </SmallModal>
      )}

      {showTransfer && (
        <SmallModal title="Transferencia" onClose={()=>setShowTransfer(false)}>
          <TransferForm onSubmit={handleTransfer} onCancel={()=>setShowTransfer(false)} />
        </SmallModal>
      )}

      {showAdjust && active && (
        <SmallModal title={`Ajuste - ${active.name}`} onClose={()=>setShowAdjust(false)}>
          <AdjustForm onSubmit={(qty,reason)=>handleAdjust(qty,reason)} onCancel={()=>setShowAdjust(false)} />
        </SmallModal>
      )}

      {active && history && history.length>0 && (
        <div style={{marginTop:12}}>
          <h4>Historial de {active.name}</h4>
          <ul>
            {history.map((h,i)=>(<li key={i}>{h.type || h.action} - {h.qty ?? ''} {h.note || ''}</li>))}
          </ul>
        </div>
      )}
    </section>
  )
}

function ProductForm({ onSubmit, onCancel }){
  const [sku, setSku] = useState('')
  const [name, setName] = useState('')
  const [stock, setStock] = useState(0)
  return (
    <form onSubmit={e=>{ e.preventDefault(); onSubmit({ sku, name, stock: Number(stock) }) }}>
      <div style={{marginBottom:8}}><label>SKU</label><input value={sku} onChange={e=>setSku(e.target.value)} style={{width:'100%'}} /></div>
      <div style={{marginBottom:8}}><label>Nombre</label><input value={name} onChange={e=>setName(e.target.value)} style={{width:'100%'}} /></div>
      <div style={{marginBottom:8}}><label>Stock inicial</label><input type="number" value={stock} onChange={e=>setStock(e.target.value)} style={{width:'100%'}} /></div>
      <div style={{display:'flex', justifyContent:'flex-end', gap:8}}>
        <button type="button" onClick={onCancel}>Cancelar</button>
        <button type="submit">Crear</button>
      </div>
    </form>
  )
}

function StockForm({ onSubmit, onCancel }){
  const [qty, setQty] = useState(1)
  const [warehouse, setWarehouse] = useState('almacen-principal')
  return (
    <form onSubmit={e=>{ e.preventDefault(); onSubmit(Number(qty), warehouse) }}>
      <div style={{marginBottom:8}}><label>Cantidad</label><input type="number" value={qty} onChange={e=>setQty(e.target.value)} style={{width:'100%'}} /></div>
      <div style={{marginBottom:8}}><label>Almacén</label><input value={warehouse} onChange={e=>setWarehouse(e.target.value)} style={{width:'100%'}} /></div>
      <div style={{display:'flex', justifyContent:'flex-end', gap:8}}>
        <button type="button" onClick={onCancel}>Cancelar</button>
        <button type="submit">Aceptar</button>
      </div>
    </form>
  )
}

function TransferForm({ onSubmit, onCancel }){
  const [from, setFrom] = useState('almacen-principal')
  const [to, setTo] = useState('almacen-secundario')
  const [sku, setSku] = useState('')
  const [qty, setQty] = useState(1)
  return (
    <form onSubmit={e=>{ e.preventDefault(); onSubmit(from,to,sku,Number(qty)) }}>
      <div style={{marginBottom:8}}><label>SKU</label><input value={sku} onChange={e=>setSku(e.target.value)} style={{width:'100%'}} /></div>
      <div style={{display:'flex', gap:8}}>
        <div style={{flex:1}}><label>Desde</label><input value={from} onChange={e=>setFrom(e.target.value)} style={{width:'100%'}} /></div>
        <div style={{flex:1}}><label>Hacia</label><input value={to} onChange={e=>setTo(e.target.value)} style={{width:'100%'}} /></div>
      </div>
      <div style={{marginTop:8}}><label>Cantidad</label><input type="number" value={qty} onChange={e=>setQty(e.target.value)} style={{width:'100%'}} /></div>
      <div style={{display:'flex', justifyContent:'flex-end', gap:8, marginTop:8}}>
        <button type="button" onClick={onCancel}>Cancelar</button>
        <button type="submit">Transferir</button>
      </div>
    </form>
  )
}

function AdjustForm({ onSubmit, onCancel }){
  const [qty, setQty] = useState(0)
  const [reason, setReason] = useState('')
  return (
    <form onSubmit={e=>{ e.preventDefault(); onSubmit(Number(qty), reason) }}>
      <div style={{marginBottom:8}}><label>Delta (positivo/negativo)</label><input type="number" value={qty} onChange={e=>setQty(e.target.value)} style={{width:'100%'}} /></div>
      <div style={{marginBottom:8}}><label>Motivo</label><input value={reason} onChange={e=>setReason(e.target.value)} style={{width:'100%'}} /></div>
      <div style={{display:'flex', justifyContent:'flex-end', gap:8}}>
        <button type="button" onClick={onCancel}>Cancelar</button>
        <button type="submit">Aplicar</button>
      </div>
    </form>
  )
}

