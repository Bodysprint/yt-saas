import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import { API_URL } from "../config";
import { useAuth } from "../components/AuthContext";

function Dashboard() {
  const { user, logout } = useAuth();
  const [channelUrl, setChannelUrl] = useState("");
  const [videos, setVideos] = useState([]);
  const [selectedVideos, setSelectedVideos] = useState([]);
  const [files, setFiles] = useState([]);
  const [isScraping, setIsScraping] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [scrapingProgress, setScrapingProgress] = useState(0);
  const [transcriptionProgress, setTranscriptionProgress] = useState(0);
  const [transcriptionCompleted, setTranscriptionCompleted] = useState(false);
  const [transcriptionStarted, setTranscriptionStarted] = useState(false);

  // Ne pas charger les URLs scrapées au chargement - dashboard vierge
  useEffect(() => {
    // Dashboard vierge au chargement
    setVideos([]);
    setFiles([]);
    setTranscriptionCompleted(false);
    setTranscriptionStarted(false);
    setIsTranscribing(false);
  }, []);

  /** Scraper la chaîne */
  const scrapeChannel = async () => {
    if (!channelUrl.trim()) {
      toast.error("Veuillez entrer une URL de chaîne YouTube");
      return;
    }

    // Nettoyer complètement l'état avant de commencer
    setVideos([]);
    setFiles([]);
    setSelectedVideos([]);
    setTranscriptionCompleted(false);
    setTranscriptionStarted(false);
    setIsTranscribing(false);

    setIsScraping(true);
    setScrapingProgress(0);

    try {
      const res = await fetch(`${API_URL}/api/scrape/channel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel: channelUrl }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Erreur API scrape");
      }

      const data = await res.json();
      
      if (data.status === "started") {
        toast.success("Scraping démarré ! Les vidéos apparaîtront au fur et à mesure...");
        
        // Progression initiale
        setScrapingProgress(5);
        
        // Charger immédiatement les URLs existantes (avec titres réels)
        const loadInitialUrls = async () => {
          try {
            const urlsRes = await fetch(`${API_URL}/api/scrape/urls`);
            if (urlsRes.ok) {
              const urlsData = await urlsRes.json();
              if (urlsData.urls && urlsData.urls.length > 0) {
                const videoList = urlsData.urls.map((video, index) => ({
                  id: index,
                  url: video.url,
                  title: video.title,
                  videoId: video.video_id,
                  thumbnail: video.thumbnail
                }));
                setVideos(videoList);
                const progress = Math.min(95, Math.max(10, (urlsData.urls.length / 30) * 100));
                setScrapingProgress(progress);
                console.log(`🚀 URLs initiales chargées INSTANTANÉMENT avec titres réels: ${urlsData.urls.length}`);
              }
            }
          } catch (err) {
            console.error("Erreur chargement initial:", err);
          }
        };
        loadInitialUrls();
        
        let pollUrls, pollStatus, progressInterval;
        
        // Démarrer le polling pour les URLs (plus fréquent) - VERSION RAPIDE
        pollUrls = setInterval(async () => {
          try {
            const urlsRes = await fetch(`${API_URL}/api/scrape/urls`);
            if (urlsRes.ok) {
              const urlsData = await urlsRes.json();
              console.log(`DEBUG Frontend: Réponse API RAPIDE - ${urlsData.urls ? urlsData.urls.length : 0} URLs`);
              
              if (urlsData.urls && urlsData.urls.length > 0) {
                const videoList = urlsData.urls.map((video, index) => ({
                  id: index,
                  url: video.url,
                  title: video.title,
                  videoId: video.video_id,
                  thumbnail: video.thumbnail
                }));
                setVideos(videoList);
                // Mettre à jour la progression basée sur le nombre d'URLs trouvées
                const progress = Math.min(95, Math.max(10, (urlsData.urls.length / 30) * 100)); // Minimum 10%, max 95%
                setScrapingProgress(progress);
                console.log(`⚡ URLs affichées INSTANTANÉMENT avec titres réels: ${urlsData.urls.length}, Progression: ${progress}%`);
              } else {
                // Aucune URL encore trouvée, progression minimale
                setScrapingProgress(5);
                console.log("⏳ Aucune URL trouvée encore...");
              }
            } else {
              console.error("❌ Erreur API URLs:", urlsRes.status);
            }
          } catch (err) {
            console.error("❌ Erreur polling URLs:", err);
          }
        }, 1000); // Polling à 1 seconde pour éviter la surcharge

        // Démarrer le polling pour le statut
        pollStatus = setInterval(async () => {
          try {
            const statusRes = await fetch(`${API_URL}/api/scrape/status`);
            if (statusRes.ok) {
              const statusData = await statusRes.json();
              
              // Mettre à jour la progression même si le processus est en cours
              if (statusData.running && statusData.count > 0) {
                const progress = Math.min(95, Math.max(10, (statusData.count / 30) * 100));
                setScrapingProgress(progress);
                console.log(`Statut: ${statusData.count} URLs, Progression: ${progress}%`);
              }
              
              if (!statusData.running) {
                // Scraping terminé - arrêter tous les polling
                clearInterval(pollStatus);
                clearInterval(pollUrls);
      clearInterval(progressInterval);
      setScrapingProgress(100);
                setIsScraping(false);
                
                // Charger les URLs finales une dernière fois
                const finalUrlsRes = await fetch(`${API_URL}/api/scrape/urls`);
                if (finalUrlsRes.ok) {
                  const finalUrlsData = await finalUrlsRes.json();
                  if (finalUrlsData.urls && finalUrlsData.urls.length > 0) {
                    const videoList = finalUrlsData.urls.map((video, index) => ({
                      id: index,
                      url: video.url,
                      title: video.title,
                      videoId: video.video_id,
                      thumbnail: video.thumbnail
                    }));
                    setVideos(videoList);
                    toast.success(`Scraping terminé ! ${finalUrlsData.count} vidéos trouvées avec titres réels.`);
                  } else {
                    setVideos([]);
                    toast.success("Scraping terminé mais aucune vidéo trouvée.");
                  }
                }
              }
            }
          } catch (err) {
            console.error("Erreur polling statut:", err);
          }
        }, 500); // Polling plus fréquent (0.5 seconde)

        // Progression de base qui s'incrémente même sans URLs
        let baseProgress = 5;
        progressInterval = setInterval(() => {
          if (isScraping) {
            baseProgress = Math.min(85, baseProgress + 2); // Incrémenter de 2% toutes les secondes
            setScrapingProgress(baseProgress);
            console.log(`Progression de base: ${baseProgress}%`);
          }
        }, 1000);

        // Arrêter le polling après 3 minutes maximum
        setTimeout(() => {
          clearInterval(pollStatus);
          clearInterval(pollUrls);
          clearInterval(progressInterval);
          if (isScraping) {
            setIsScraping(false);
            setScrapingProgress(100);
            toast.info("Scraping terminé (timeout)");
          }
        }, 180000); // 3 minutes

      } else {
        toast.error("Erreur lors du démarrage du scraping");
        setIsScraping(false);
        setScrapingProgress(0);
      }

    } catch (err) {
      toast.error(`Échec du scraping: ${err.message}`);
      console.error(err);
        setIsScraping(false);
        setScrapingProgress(0);
    }
  };


  /** Gérer la sélection des vidéos */
  const toggleVideoSelection = (videoId) => {
    setSelectedVideos(prev => 
      prev.includes(videoId) 
        ? prev.filter(id => id !== videoId)
        : [...prev, videoId]
    );
  };

  const selectAllVideos = () => {
    setSelectedVideos(videos.map(video => video.id));
  };

  const deselectAllVideos = () => {
    setSelectedVideos([]);
  };

  /** Transcrire les vidéos sélectionnées */
  const transcribe = async () => {
    if (selectedVideos.length === 0) {
      toast.error("Veuillez sélectionner au moins une vidéo à transcrire");
      return;
    }

    // Nettoyer l'état avant de commencer
    setFiles([]);
    setTranscriptionCompleted(false);
    setTranscriptionStarted(false);
    setIsTranscribing(true);
    setTranscriptionProgress(0);

    try {
      // Nettoyer les anciens fichiers de transcription
      await fetch(`${API_URL}/api/transcripts/clean`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });

      // Récupérer les URLs des vidéos sélectionnées
      const selectedUrls = videos
        .filter(video => selectedVideos.includes(video.id))
        .map(video => video.url);

      const res = await fetch(`${API_URL}/api/transcribe/selected`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ urls: selectedUrls }),
      });

      if (!res.ok) {
        const errData = await res.json();
        console.error("Erreur détaillée:", errData);
        throw new Error(errData.error || `Erreur API transcribe (${res.status})`);
      }

      const data = await res.json();
      
      if (data.status === "started") {
        toast.success(`Transcription démarrée ! Le navigateur va s'ouvrir pour traiter ${selectedVideos.length} vidéo(s).`);
        
        // Démarrer le polling pour le statut de transcription
        const pollTranscribe = setInterval(async () => {
          try {
            const statusRes = await fetch(`${API_URL}/api/transcribe/status`);
            if (statusRes.ok) {
              const statusData = await statusRes.json();
              
              // Mettre à jour la progression basée sur les fichiers générés
              if (statusData.running) {
                const progress = Math.min(95, (statusData.filesCount / selectedVideos.length) * 100);
                setTranscriptionProgress(progress);
              } else {
                // Transcription terminée
                clearInterval(pollTranscribe);
                setTranscriptionProgress(100);
                setTranscriptionCompleted(true);
                setIsTranscribing(false);
                
                // Recharger la liste des fichiers
      await listFiles();
                
                toast.success(`🎉 Transcription terminée ! ${statusData.filesCount} fichier(s) généré(s).`);
              }
            }
          } catch (err) {
            console.error("Erreur polling transcription:", err);
          }
        }, 1000); // Polling plus fréquent

        // Arrêter le polling après 15 minutes maximum
        setTimeout(() => {
          clearInterval(pollTranscribe);
          if (isTranscribing) {
            setTranscriptionProgress(100);
            setTranscriptionCompleted(true);
            setIsTranscribing(false);
            toast.info("Transcription terminée (timeout)");
            listFiles(); // Recharger les fichiers
          }
        }, 900000); // 15 minutes

      } else {
        toast.error("Erreur lors du démarrage de la transcription");
        setIsTranscribing(false);
        setTranscriptionStarted(false);
      }

    } catch (err) {
      toast.error(`Échec transcription: ${err.message}`);
      console.error(err);
      setIsTranscribing(false);
      setTranscriptionStarted(false);
    }
  };

  /** Transcrire toutes les vidéos (bulk) */
  const transcribeBulk = async () => {
    if (videos.length === 0) {
      toast.error("Aucune vidéo à transcrire. Scrapez d'abord une chaîne.");
      return;
    }

    // Nettoyer l'état avant de commencer
    setFiles([]);
    setTranscriptionCompleted(false);
    setTranscriptionStarted(false);
    setIsTranscribing(true);
    setTranscriptionProgress(0);

    try {
      // Nettoyer les anciens fichiers de transcription
      await fetch(`${API_URL}/api/transcripts/clean`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });

      const res = await fetch(`${API_URL}/api/transcribe/bulk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });

      if (!res.ok) {
        const errData = await res.json();
        console.error("Erreur détaillée:", errData);
        throw new Error(errData.error || `Erreur API transcribe bulk (${res.status})`);
      }

      const data = await res.json();
      
      if (data.status === "started") {
        toast.success(`Transcription démarrée ! Le navigateur va s'ouvrir pour traiter ${videos.length} vidéo(s).`);
        
        // Démarrer le polling pour le statut de transcription
        const pollTranscribe = setInterval(async () => {
          try {
            const statusRes = await fetch(`${API_URL}/api/transcribe/status`);
            if (statusRes.ok) {
              const statusData = await statusRes.json();
              
              // Mettre à jour la progression basée sur les fichiers générés
              if (statusData.running) {
                const progress = Math.min(95, (statusData.filesCount / videos.length) * 100);
                setTranscriptionProgress(progress);
              } else {
                // Transcription terminée
                clearInterval(pollTranscribe);
                setTranscriptionProgress(100);
                setTranscriptionCompleted(true);
                setIsTranscribing(false);
                
                // Recharger la liste des fichiers
                await listFiles();
                
                toast.success(`🎉 Transcription terminée ! ${statusData.filesCount} fichier(s) généré(s).`);
              }
            }
          } catch (err) {
            console.error("Erreur polling transcription:", err);
          }
        }, 1000); // Polling plus fréquent

        // Arrêter le polling après 15 minutes maximum
        setTimeout(() => {
          clearInterval(pollTranscribe);
          if (isTranscribing) {
            setTranscriptionProgress(100);
            setTranscriptionCompleted(true);
            setIsTranscribing(false);
            toast.info("Transcription terminée (timeout)");
            listFiles(); // Recharger les fichiers
          }
        }, 900000); // 15 minutes
        
      } else {
        toast.warning("Statut de transcription inattendu");
        setIsTranscribing(false);
      }

    } catch (error) {
      console.error("Erreur lors de la transcription bulk:", error);
      toast.error(`Erreur: ${error.message}`);
      setIsTranscribing(false);
      setTranscriptionStarted(false);
    }
  };

  /** Lister les fichiers */
  const listFiles = async () => {
    try {
      const res = await fetch(`${API_URL}/api/transcripts`);
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Erreur API list_files");
      }

      const data = await res.json();
      setFiles(data.files || []);
    } catch (err) {
      toast.error(`Impossible de lister les fichiers: ${err.message}`);
      console.error(err);
    }
  };

  /** Rafraîchir la liste des vidéos scrapées */
  const refreshScrapedVideos = async () => {
    try {
      const res = await fetch(`${API_URL}/api/scraped-urls`);
      if (res.ok) {
        const data = await res.json();
        if (data.videos && data.videos.length > 0) {
          const videoList = data.videos.map((video, index) => ({
            id: index,
            url: video.url,
            title: video.title,
            videoId: video.video_id,
            thumbnail: video.thumbnail
          }));
          setVideos(videoList);
          toast.success(`${data.videos.length} vidéos chargées`);
        } else {
          setVideos([]);
          toast.success("Aucune vidéo trouvée");
        }
      } else {
        setVideos([]);
        toast.success("Liste vidée");
      }
    } catch (err) {
      console.error("Erreur lors du rafraîchissement:", err);
      setVideos([]);
      toast.success("Liste vidée");
    }
  };

  /** Charger les URLs scrapées existantes */
  const loadScrapedUrls = async () => {
    try {
      const res = await fetch(`${API_URL}/api/scraped-urls`);
      if (res.ok) {
        const data = await res.json();
        if (data.videos && data.videos.length > 0) {
          const videoList = data.videos.map((video, index) => ({
            id: index,
            url: video.url,
            title: video.title,
            videoId: video.video_id,
            thumbnail: video.thumbnail
          }));
          setVideos(videoList);
        }
      }
    } catch (err) {
      console.error("Erreur lors du chargement des URLs:", err);
    }
  };

  /** Télécharger tous les fichiers de transcription */
  const downloadTranscripts = () => {
    window.open(`${API_URL}/api/transcripts/download`, '_blank');
  };

  /** Voir les logs de la session */
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState("");

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_URL}/api/logs`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs);
        setShowLogs(true);
      } else {
        toast.error("Impossible de récupérer les logs");
      }
    } catch (err) {
      toast.error(`Erreur logs: ${err.message}`);
    }
  };

  /** Debug transcription */
  const debugTranscription = async () => {
    try {
      console.log("🔧 Debug transcription...");
      
      // Vérifier les URLs
      const urlsRes = await fetch(`${API_URL}/api/debug/urls`);
      if (urlsRes.ok) {
        const urlsData = await urlsRes.json();
        console.log("URLs debug:", urlsData);
        toast.info(`URLs: ${urlsData.count} trouvées`);
      }
      
      // Vérifier les transcripts
      const transcriptsRes = await fetch(`${API_URL}/api/debug/transcripts`);
      if (transcriptsRes.ok) {
        const transcriptsData = await transcriptsRes.json();
        console.log("Transcripts debug:", transcriptsData);
        toast.info(`Transcripts: ${transcriptsData.count} fichiers`);
      }
      
      // Vérifier le statut de transcription
      const statusRes = await fetch(`${API_URL}/api/transcribe/status`);
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        console.log("Status transcription:", statusData);
        toast.info(`Transcription: ${statusData.running ? 'En cours' : 'Arrêtée'}, ${statusData.filesCount} fichiers`);
      }
      
    } catch (err) {
      console.error("Erreur debug:", err);
      toast.error(`Erreur debug: ${err.message}`);
    }
  };


  /** Afficher le contenu d'un fichier */
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState("");

  const viewFileContent = async (filePath) => {
    try {
      const res = await fetch(`${API_URL}/api/transcripts/content?path=${encodeURIComponent(filePath)}`);
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Erreur lors de la lecture du fichier");
      }

      const data = await res.json();
      setSelectedFile(filePath);
      setFileContent(data.content);
    } catch (err) {
      toast.error(`Impossible de lire le fichier: ${err.message}`);
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Bonjour, <span className="font-medium">{user?.email}</span>
              </span>
              <button onClick={logout} className="btn-danger text-sm">
                Déconnexion
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Scraper */}
        <div className="card mb-8">
          <h2 className="text-xl font-semibold mb-2">Scraper une chaîne YouTube</h2>
          <p className="text-gray-600 mb-4">Entrez l'URL d'une chaîne pour extraire ses vidéos</p>

          <div className="flex gap-4 mb-6">
            <input
              type="url"
              value={channelUrl}
              onChange={(e) => setChannelUrl(e.target.value)}
              placeholder="https://www.youtube.com/@nomdelachaine"
              className="input-field flex-1"
            />
            <button
              onClick={scrapeChannel}
              className="btn-primary"
              disabled={!channelUrl.trim() || isScraping}
            >
              {isScraping ? "Scraping..." : "Scraper"}
            </button>
          </div>

          {isScraping && (
            <div className="mt-2">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Scraping en cours...</span>
                <span>{Math.round(scrapingProgress)}%</span>
              </div>
              <div className="w-full bg-gray-200 h-2 rounded-full">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all"
                  style={{ width: `${scrapingProgress}%` }}
                ></div>
              </div>
            </div>
          )}

        </div>

        {/* Liste des vidéos scrapées */}
          {videos.length > 0 && (
          <div className="card mb-8">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Vidéos scrapées ({videos.length})</h3>
              <div className="flex gap-2">
                <button
                  onClick={selectAllVideos}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                    Tout sélectionner
                  </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={deselectAllVideos}
                  className="text-sm text-gray-600 hover:text-gray-700"
                >
                    Tout désélectionner
                  </button>
                </div>
              </div>
            <div className="max-h-64 overflow-y-auto grid gap-3">
              {videos.map((video) => (
                <div key={video.id} className="flex items-center bg-gray-50 p-3 rounded">
                  {/* Case à cocher */}
                    <input
                      type="checkbox"
                    checked={selectedVideos.includes(video.id)}
                    onChange={() => toggleVideoSelection(video.id)}
                    className="mr-3 w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                  />
                  
                  {/* Miniature */}
                  {video.thumbnail && (
                    <img
                      src={video.thumbnail}
                      alt={video.title}
                      className="w-16 h-12 object-cover rounded mr-3 flex-shrink-0"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  )}
                  
                  {/* Infos vidéo */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{video.title}</p>
                    <p className="text-xs text-gray-500 truncate">{video.url}</p>
                  </div>
                  
                  {/* Bouton Voir */}
                  <a
                    href={video.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-primary text-xs px-3 py-1 ml-2 flex-shrink-0"
                  >
                    Voir
                  </a>
                    </div>
                ))}
              </div>
            </div>
          )}

        {/* Actions */}
          <div className="card mb-8">
            <h3 className="text-lg font-medium mb-4">Actions</h3>
          <div className="flex gap-3 flex-wrap items-center">
              <button
                onClick={transcribe}
                className="btn-success"
              disabled={isTranscribing || selectedVideos.length === 0}
              >
              {isTranscribing 
                ? `Transcription... (${selectedVideos.length})` 
                : `Transcrire sélectionnées (${selectedVideos.length})`
              }
              </button>
              
              <button
                onClick={transcribeBulk}
                className="btn-primary"
                disabled={isTranscribing || videos.length === 0}
              >
                {isTranscribing 
                  ? `Transcription... (${videos.length})` 
                  : `Transcrire tout (${videos.length})`
                }
              </button>
              
            <button onClick={refreshScrapedVideos} className="btn-secondary">
              Rafraîchir la liste
            </button>
            <button onClick={fetchLogs} className="btn-secondary">
              📋 Voir les logs
              </button>
            <button onClick={debugTranscription} className="btn-secondary">
              🔧 Debug transcription
              </button>
            {transcriptionCompleted && files.length > 0 && (
              <button onClick={downloadTranscripts} className="btn-primary">
                📥 Télécharger tout ({files.length} fichiers)
              </button>
            )}
            {selectedVideos.length > 0 && (
              <span className="text-sm text-gray-600">
                {selectedVideos.length} vidéo(s) sélectionnée(s)
              </span>
            )}
          </div>

          {/* Barre de progression de transcription */}
          {isTranscribing && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Transcription en cours...</span>
                <span>{Math.round(transcriptionProgress)}%</span>
              </div>
              <div className="w-full bg-gray-200 h-2 rounded-full">
                <div
                  className="bg-green-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${transcriptionProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* Message de statut */}
          {transcriptionCompleted && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center">
                <span className="text-green-600 mr-2">✅</span>
                <span className="text-green-800 font-medium">
                  Transcription terminée ! {files.length} fichier(s) généré(s).
                </span>
            </div>
          </div>
        )}
        </div>

        {/* Liste des fichiers */}
        {files.length > 0 && (
          <div className="card">
            <h3 className="text-lg font-medium mb-4">Fichiers générés ({files.length})</h3>
            <div className="grid gap-2">
              {files.map((file, i) => (
                <div key={i} className="flex items-center justify-between bg-gray-50 p-3 rounded">
                  <div className="flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    <span className="text-sm font-medium">{file.name}</span>
                    <span className="text-xs text-gray-500 ml-2">
                      ({Math.round(file.size / 1024)} KB)
                    </span>
                  </div>
                  <button
                    onClick={() => viewFileContent(file.path)}
                    className="btn-primary text-xs px-3 py-1"
                  >
                    Voir le contenu
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Affichage du contenu d'un fichier */}
        {selectedFile && (
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Contenu: {selectedFile}</h3>
              <button
                onClick={() => setSelectedFile(null)}
                className="btn-secondary text-sm px-3 py-1"
              >
                Fermer
              </button>
            </div>
            <div className="bg-gray-100 p-4 rounded max-h-96 overflow-y-auto">
              <pre className="text-sm whitespace-pre-wrap">{fileContent}</pre>
            </div>
          </div>
        )}

        {videos.length === 0 && files.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            🚀 Commencez par scraper une chaîne YouTube pour voir les vidéos, puis lancez la transcription pour voir les fichiers générés.
          </div>
        )}

        {/* Modal des logs */}
        {showLogs && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-4xl max-h-96 w-full mx-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium">Logs de la session</h3>
                <button
                  onClick={() => setShowLogs(false)}
                  className="btn-secondary text-sm px-3 py-1"
                >
                  Fermer
                </button>
              </div>
              <div className="bg-gray-100 p-4 rounded max-h-80 overflow-y-auto">
                <pre className="text-xs whitespace-pre-wrap font-mono">{logs}</pre>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default Dashboard;
