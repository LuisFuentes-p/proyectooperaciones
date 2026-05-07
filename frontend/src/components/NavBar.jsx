import React from "react";
import { useAuth } from "../context/AuthContext";

export default function Navbar({ activeTab, setActiveTab }) {

  const { user, logout } = useAuth();

  const tabs = [
    "inventario",
    "comercial",
    "logistica",
    "nomina",
    "finanzas"
  ];

  return (
    <div className="bg-black text-white p-4 flex justify-between">

      <div className="flex gap-4">

        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded ${
              activeTab === tab
                ? "bg-white text-black"
                : "bg-gray-800"
            }`}
          >
            {tab}
          </button>
        ))}

      </div>

      <div className="flex gap-4 items-center">

        <span>{user?.username}</span>

        <button
          onClick={logout}
          className="bg-red-500 px-3 py-1 rounded"
        >
          Salir
        </button>

      </div>

    </div>
  );
}