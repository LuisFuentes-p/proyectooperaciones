import React from 'react'
import Inventory from '../modules/Inventory'
import Compras from '../modules/Compras'
import Finanzas from '../modules/Finanzas'
import Logistica from '../modules/Logistica'
import Nomina from '../modules/Nomina'
import Usuarios from '../modules/Usuarios'

export default function AreaView({ area, role, permissions }){
  const props = { role, permissions }
  switch(area){
    case 'Inventario': return <Inventory {...props} />
    case 'Compras': return <Compras {...props} />
    case 'Finanzas': return <Finanzas {...props} />
    case 'Logistica': return <Logistica {...props} />
    case 'Nomina': return <Nomina {...props} />
    case 'Usuarios': return <Usuarios {...props} />
    default: return <div>Área no disponible</div>
  }
}
