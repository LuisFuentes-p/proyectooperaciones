
import React, { useState } from "react";
import NavBar from "../components/NavBar";
import Inventory from "../modules/Inventory";
import Compras from "../modules/Compras";
import Finanzas from "../modules/Finanzas";
import Logistica from "../modules/Logistica";
import Nomina from "../modules/Nomina";
import { useAuth } from "../context/AuthContext";


export default function Dashboard() {

  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("inventario");

  return (
    <div className="h-screen flex flex-col">

      <NavBar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <div className="flex-1 p-6 bg-gray-100">

        {activeTab === "inventario" && <Inventory username={user?.username || "admin"} />}

        {activeTab === "comercial" && (
          <div>
            <h1 className="text-3xl font-bold">
              Compras/Ventas
            </h1>
          </div>
        )}

        {activeTab === "comercial" && <Compras />}

        {activeTab === "nomina" && <Nomina role={user?.role} permissions={user?.permissions} />}

        {activeTab === "logistica" && (
          <Logistica username={user?.username || "admin"} />
        )}

        {activeTab === "finanzas" && <Finanzas />}

      </div>

    </div>
  );
}