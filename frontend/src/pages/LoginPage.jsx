import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {

  const { login } = useAuth();

  const [username, setUsername] = useState("");
  const [role, setRole] = useState("inventario");

  const handleSubmit = (e) => {
    e.preventDefault();

    login(username, role);
  };

  return (
    <div className="h-screen flex items-center justify-center bg-gray-100">

      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded shadow w-96"
      >

        <h1 className="text-2xl font-bold mb-6">
          ERP Login
        </h1>

        <input
          type="text"
          placeholder="Usuario"
          className="w-full border p-2 mb-4"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        <select
          className="w-full border p-2 mb-4"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        >
          <option value="inventario">Inventario</option>
          <option value="comercial">Compras/Ventas</option>
          <option value="logistica">Logística</option>
          <option value="nomina">Nómina</option>
          <option value="finanzas">Finanzas</option>
        </select>

        <button
          className="w-full bg-black text-white p-2 rounded"
        >
          Entrar
        </button>

      </form>

    </div>
  );
}