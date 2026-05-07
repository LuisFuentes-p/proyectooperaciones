
import { useState } from "react";
import NavBar from "../components/NavBar";

export default function Dashboard() {

  const [activeTab, setActiveTab] = useState("inventario");

  return (
    <div className="h-screen flex flex-col">

      <NavBar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <div className="flex-1 p-6 bg-gray-100">

        {activeTab === "inventario" && (
          <div>
            <h1 className="text-3xl font-bold">
              Inventario
            </h1>
          </div>
        )}

        {activeTab === "comercial" && (
          <div>
            <h1 className="text-3xl font-bold">
              Compras/Ventas
            </h1>
          </div>
        )}

        {activeTab === "logistica" && (
          <div>
            <h1 className="text-3xl font-bold">
              Logística
            </h1>
          </div>
        )}

        {activeTab === "nomina" && (
          <div>
            <h1 className="text-3xl font-bold">
              Nómina
            </h1>
          </div>
        )}

        {activeTab === "finanzas" && (
          <div>
            <h1 className="text-3xl font-bold">
              Finanzas
            </h1>
          </div>
        )}

      </div>

    </div>
  );
}