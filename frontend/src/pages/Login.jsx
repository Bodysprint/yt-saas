// src/pages/Login.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../components/AuthContext";
import { API_URL } from "../config";
import toast from "react-hot-toast";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log("🔵 handleSubmit appelé !");
    
    // Validation côté client
    if (!email || !email.includes('@')) {
      toast.error("Veuillez entrer une adresse email valide");
      return;
    }
    
    if (!password) {
      toast.error("Veuillez entrer votre mot de passe");
      return;
    }
    
    setIsLoading(true);
    
    try {
      console.log("Tentative de connexion pour:", email);
      console.log("URL de l'API:", `${API_URL}/api/auth/login`);
      
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      console.log("Réponse du serveur:", res.status, res.statusText);

      if (!res.ok) {
        const errorData = await res.json();
        console.error("Erreur du serveur:", errorData);
        
        // Messages d'erreur plus spécifiques
        if (res.status === 400) {
          toast.error("Email ou mot de passe requis");
        } else if (res.status === 401) {
          toast.error("Mot de passe incorrect");
        } else if (res.status === 404) {
          toast.error("Utilisateur non trouvé");
        } else if (res.status === 500) {
          toast.error("Erreur du serveur, veuillez réessayer");
        } else {
          toast.error(errorData.error || "Erreur de connexion");
        }
        return;
      }

      const data = await res.json();
      console.log("Données reçues:", data);
      
      // Le backend Flask retourne {message, token, user: {email}}
      const userData = { 
        email: data.user.email, 
        token: data.token
      };

      login(userData);
      toast.success("Connexion réussie !");
      navigate("/dashboard");
    } catch (err) {
      console.error("Erreur de connexion:", err);
      toast.error("Erreur de connexion - Vérifiez que le serveur est démarré");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="card">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Connexion</h2>
            <p className="text-gray-600 mb-8">Connectez-vous à votre compte</p>
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
                placeholder="Votre mot de passe"
                className="input-field"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              className="w-full btn-primary"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <svg className="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Connexion...
                </>
              ) : (
                "Se connecter"
              )}
            </button>
          </form>
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Pas de compte ?{" "}
              <a href="/register" className="text-primary-600 hover:text-primary-500 font-medium">
                Créer un compte
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
