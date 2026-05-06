export class AccessMatrix {
  static demoUsers = [
    { username: 'admin', displayName: 'Administrador', role: 'admin' },
    { username: 'compras', displayName: 'Jefe de Compras', role: 'compras' },
    { username: 'ventas', displayName: 'Jefe de Ventas', role: 'ventas' },
    { username: 'inventario', displayName: 'Jefe de Inventario', role: 'inventario' },
    { username: 'auditor', displayName: 'Auditor Operativo', role: 'auditor' },
  ];

  static areas = [
    {
      id: 'finanzas',
      label: 'Finanzas',
      description: 'Reportes, tracking de PDFs e indicadores financieros.',
      permission: 'finanzas',
    },
    {
      id: 'compras',
      label: 'Compras',
      description: 'Portal de abastecimiento y órdenes de compra.',
      permission: 'compras',
    },
    {
      id: 'ventas',
      label: 'Ventas',
      description: 'Portal de ventas y facturación de clientes.',
      permission: 'ventas',
    },
    {
      id: 'inventario',
      label: 'Inventario',
      description: 'Control de stock, entradas y salidas.',
      permission: 'inventario',
    },
    {
      id: 'devoluciones',
      label: 'Devoluciones',
      description: 'Registro y seguimiento de devoluciones.',
      permission: 'devoluciones',
    },
    {
      id: 'usuarios',
      label: 'Usuarios',
      description: 'Administracion de usuarios y roles.',
      permission: 'usuarios',
    },
  ];

  static permissionsByRole = {
    admin: ['finanzas', 'compras', 'ventas', 'inventario', 'devoluciones', 'usuarios'],
    compras: ['finanzas', 'compras', 'inventario'],
    ventas: ['finanzas', 'ventas', 'inventario'],
    inventario: ['finanzas', 'inventario'],
    auditor: ['finanzas', 'devoluciones'],
  };

  static getRole(username) {
    return this.demoUsers.find((user) => user.username === username)?.role ?? 'viewer';
  }

  static getPermissions(role) {
    return this.permissionsByRole[role] ?? [];
  }

  static hasPermission(role, permission) {
    return this.getPermissions(role).includes(permission);
  }

  static getTabs(role) {
    return this.areas.map((area) => ({
      ...area,
      enabled: this.hasPermission(role, area.permission),
    }));
  }

  static getFirstEnabledTab(role) {
    return this.getTabs(role).find((tab) => tab.enabled)?.id ?? 'finanzas';
  }
}
