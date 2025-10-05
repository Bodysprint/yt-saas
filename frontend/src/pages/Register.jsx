import { useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { useAuth } from "../components/AuthContext";
import { API_URL } from "../config";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log("🟢 handleSubmit appelé !");
    
    // Validation côté client
    if (!email || !email.includes('@') || !email.includes('.')) {
      toast.error("Veuillez entrer une adresse email valide");
      return;
    }
    
    if (!password || password.length < 4) {
      toast.error("Le mot de passe doit contenir au moins 4 caractères");
      return;
    }
    
    try {
      console.log("Tentative d'inscription pour:", email);
      console.log("URL de l'API:", `${API_URL}/api/auth/register`);
      
      const res = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      console.log("Réponse du serveur:", res.status, res.statusText);

      if (!res.ok) {
        const errorData = await res.json();
        console.error("Erreur du serveur:", errorData);
        throw new Error(errorData.error || "Échec de l'inscription");
      }

      const data = await res.json();
      console.log("Données reçues:", data);

      // Inscription réussie, mais ne pas connecter automatiquement
      toast.success("Inscription réussie ! Veuillez vous connecter.");
      navigate("/login");
    } catch (err) {
      console.error("Erreur d'inscription:", err);
      toast.error(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="card">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Inscription</h2>
            <p className="text-gray-600 mb-8">Créez votre compte pour commencer</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Adresse email
              </label>
              <input
                id="email"
                type="email"
                placeholder="votre@email.com"
                className="input-field"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                Mot de passe
              </label>
              <input
                id="password"
                type="password"
                placeholder="Choisissez un mot de passe"
                className="input-field"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              className="w-full btn-primary"
            >
              Créer mon compte
            </button>
          </form>
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Déjà un compte ?{" "}
              <a href="/login" className="text-primary-600 hover:text-primary-500 font-medium">
                Se connecter
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
