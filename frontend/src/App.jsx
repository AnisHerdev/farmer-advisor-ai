import React, { useState, useEffect, useRef } from 'react';
import {
  Sprout,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Search,
  BookOpen,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Layers,
  ArrowRight,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';

const LANGUAGES = [
  { code: 'hi', name: 'Hindi', native: 'हिन्दी', bcp47: 'hi-IN' },
  { code: 'en', name: 'English', native: 'English', bcp47: 'en-IN' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు', bcp47: 'te-IN' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்', bcp47: 'ta-IN' },
  { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ', bcp47: 'kn-IN' },
  { code: 'mr', name: 'Marathi', native: 'मराठी', bcp47: 'mr-IN' },
  { code: 'pa', name: 'Punjabi', native: 'ਪੰਜਾਬੀ', bcp47: 'pa-IN' },
];

export default function App() {
  const [selectedLang, setSelectedLang] = useState('hi');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [advisoryData, setAdvisoryData] = useState(null);
  const [quickPrompts, setQuickPrompts] = useState([]);
  const [showSources, setShowSources] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [executionMode, setExecutionMode] = useState('demo');
  const [backendStatus, setBackendStatus] = useState('checking');
  const [errorMsg, setErrorMsg] = useState(null);
  const [showArchitecture, setShowArchitecture] = useState(false);

  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  // Fetch initial health and quick prompts
  useEffect(() => {
    checkHealth();
    fetchQuickPrompts(selectedLang);
  }, [selectedLang]);

  const checkHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setBackendStatus(data.status === 'online' ? 'online' : 'degraded');
      } else {
        setBackendStatus('offline');
      }
    } catch {
      setBackendStatus('offline');
    }
  };

  const fetchQuickPrompts = async (lang) => {
    try {
      const res = await fetch(`/api/quick-prompts?lang=${lang}`);
      if (res.ok) {
        const data = await res.json();
        setQuickPrompts(data);
      }
    } catch (e) {
      console.warn("Could not fetch quick prompts:", e);
    }
  };

  // Web Speech API: Voice Input (STT)
  const toggleSpeechRecognition = () => {
    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Firefox.");
      return;
    }

    const recognition = new SpeechRecognition();
    const currentLangObj = LANGUAGES.find((l) => l.code === selectedLang) || LANGUAGES[0];
    recognition.lang = currentLangObj.bcp47;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setErrorMsg(null);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
      setIsListening(false);
      // Auto submit on voice input for friction-free farmer experience
      submitQuery(transcript, selectedLang);
    };

    recognition.onerror = (event) => {
      console.warn("Speech recognition notice:", event.error);
      setIsListening(false);
      if (event.error === 'network') {
        setErrorMsg("Voice input in Chrome requires an active connection to Google's cloud speech service. You can type your query in your language directly or click one of the quick question chips below.");
      } else if (event.error === 'not-allowed') {
        setErrorMsg("Microphone permission was denied. Please allow microphone access in your browser address bar.");
      } else if (event.error !== 'no-speech') {
        setErrorMsg(`Voice input status: ${event.error}. You can type your query directly.`);
      }
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  // Web Speech API: Audio Read-Aloud (TTS)
  const toggleAudioReadAloud = (textToSpeak) => {
    if (!synthRef.current) return;

    if (isPlayingAudio) {
      synthRef.current.cancel();
      setIsPlayingAudio(false);
      return;
    }

    // Clean markdown bold and bullet markers for speech
    const cleanText = textToSpeak.replace(/[*#•⚠️]/g, '').trim();
    const utterance = new SpeechSynthesisUtterance(cleanText);
    const currentLangObj = LANGUAGES.find((l) => l.code === selectedLang) || LANGUAGES[0];
    utterance.lang = currentLangObj.bcp47;
    utterance.rate = 0.95; // Slightly slower, calm cadence for elderly farmers

    utterance.onend = () => setIsPlayingAudio(false);
    utterance.onerror = () => setIsPlayingAudio(false);

    synthRef.current.cancel();
    synthRef.current.speak(utterance);
    setIsPlayingAudio(true);
  };

  // Submit query to backend RAG & sovereign models
  const submitQuery = async (queryText, lang) => {
    const textToSend = queryText || query;
    if (!textToSend.trim()) return;

    setLoading(true);
    setErrorMsg(null);
    if (synthRef.current) synthRef.current.cancel();
    setIsPlayingAudio(false);

    try {
      const response = await fetch('/api/advisory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: textToSend.trim(),
          language: lang || selectedLang,
          mode: executionMode
        })
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      setAdvisoryData(data);
    } catch (err) {
      console.error("Advisory error:", err);
      setErrorMsg("Unable to reach advisory engine. Please verify the backend is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  const handlePromptClick = (promptQuery) => {
    setQuery(promptQuery);
    submitQuery(promptQuery, selectedLang);
  };

  const currentLangObj = LANGUAGES.find((l) => l.code === selectedLang) || LANGUAGES[0];

  return (
    <div className="min-h-screen bg-soil-50 text-soil-900 flex flex-col antialiased">
      {/* 1. Header Bar */}
      <header className="border-b border-soil-200 bg-white/95 sticky top-0 z-30 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-forest-700 text-white flex items-center justify-center shadow-sm">
              <Sprout className="w-5 h-5 text-forest-100" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold tracking-tight text-forest-900">
                  AI Farmer Advisor
                </h1>
                <span className="text-xs px-2 py-0.5 rounded-full bg-forest-50 text-forest-700 border border-forest-200 font-medium">
                  ICAR Grounded
                </span>
              </div>
              <p className="text-xs text-soil-600 hidden sm:block">
                कृषि परामर्श एवं फसल मार्गदर्शन (Sovereign Agronomic Intelligence)
              </p>
            </div>
          </div>

          {/* Right Controls: Mode Toggle & Language Selector */}
          <div className="flex items-center gap-3">
            {/* Engine Mode Toggle */}
            <div className="hidden sm:flex items-center">
              <button
                type="button"
                onClick={() => setExecutionMode(executionMode === 'demo' ? 'local_agriparam' : 'demo')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                  executionMode === 'local_agriparam'
                    ? 'bg-forest-800 text-white border-forest-900 shadow-sm ring-2 ring-forest-300'
                    : 'bg-white hover:bg-soil-100 text-soil-700 border-soil-300'
                }`}
                title="Toggle between instant demo response and full local 2.86B AgriParam weights on CPU"
              >
                <Cpu className={`w-3.5 h-3.5 ${executionMode === 'local_agriparam' ? 'text-forest-200 animate-pulse' : 'text-forest-600'}`} />
                <span>
                  {executionMode === 'demo' ? '⚡ Fast Demo Mode' : '🧠 AgriParam CPU (2.86B)'}
                </span>
              </button>
            </div>

            {/* Language Selector */}
            <div className="relative">
              <select
                value={selectedLang}
                onChange={(e) => {
                  setSelectedLang(e.target.value);
                  if (advisoryData && query) {
                    submitQuery(query, e.target.value);
                  }
                }}
                className="appearance-none bg-soil-100 hover:bg-soil-200 text-soil-900 text-xs font-semibold py-1.5 pl-3 pr-8 rounded-lg border border-soil-300 focus:outline-none focus:ring-2 focus:ring-forest-500 cursor-pointer transition"
              >
                {LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.native} ({lang.name})
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-soil-600 absolute right-2.5 top-2.5 pointer-events-none" />
            </div>

            {/* Status Indicator */}
            <div
              className={`w-2.5 h-2.5 rounded-full ${
                backendStatus === 'online'
                  ? 'bg-forest-500 ring-2 ring-forest-200'
                  : 'bg-harvest-500 ring-2 ring-harvest-200'
              }`}
              title={`Backend: ${backendStatus}`}
            />
          </div>
        </div>
      </header>

      {/* 2. Main Content Area */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-6 py-8 flex flex-col gap-8">
        
        {/* Onboarding & Directive Hero */}
        <div className="text-center space-y-2 pt-2">
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-forest-900">
            {selectedLang === 'hi' && 'अपनी भाषा में फसल, खाद और सिंचाई की जानकारी पाएं'}
            {selectedLang === 'te' && 'మీ భాషలో పంట, ఎరువులు మరియు నీటిపారుదల సలహాలను పొందండి'}
            {selectedLang === 'ta' && 'உங்கள் மொழியில் பயிர், உரம் மற்றும் பாசன வழிகாட்டலைப் பெறுங்கள்'}
            {selectedLang === 'kn' && 'ನಿಮ್ಮ ಭಾಷೆಯಲ್ಲಿ ಬೆಳೆ, ಗೊಬ್ಬರ ಮತ್ತು ನೀರಾವರಿ ಸಲಹೆ ಪಡೆಯಿರಿ'}
            {selectedLang === 'mr' && 'तुमच्या भाषेत पीक, खत आणि सिंचनाची खात्रीशीर माहिती मिळवा'}
            {selectedLang === 'pa' && 'ਆਪਣੀ ਭਾਸ਼ਾ ਵਿੱਚ ਫਸਲ, ਖਾਦ ਅਤੇ ਸਿੰਚਾਈ ਬਾਰੇ ਸਹੀ ਜਾਣਕਾਰੀ ਪ੍ਰਾਪਤ ਕਰੋ'}
            {selectedLang === 'en' && 'Verified Crop, Fertilizer & Irrigation Guidance for Indian Farmers'}
          </h2>
          <p className="text-sm text-soil-600 max-w-xl mx-auto">
            {selectedLang === 'hi' && 'नीचे बोलकर या लिखकर पूछें, या दिए गए सुझाव पर क्लिक करें:'}
            {selectedLang === 'en' && 'Ask via voice or text in regional languages, or select a crop topic below:'}
            {selectedLang !== 'hi' && selectedLang !== 'en' && 'Speak or type your question below, or select a topic to begin:'}
          </p>
        </div>

        {/* 3. Query Input Surface with Voice Microphone */}
        <div className="relative bg-white rounded-2xl shadow-sm border border-soil-300 p-2 transition-all focus-within:border-forest-600 focus-within:ring-2 focus-within:ring-forest-100">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submitQuery(query, selectedLang);
            }}
            className="flex items-center gap-2"
          >
            <div className="pl-3 text-soil-400">
              <Search className="w-5 h-5 text-forest-700" />
            </div>

            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                selectedLang === 'hi'
                  ? 'उदा: कपास की बुवाई किस महीने में करें? या गेहूं में पहला पानी कब दें?'
                  : selectedLang === 'te'
                  ? 'ఉదా: పత్తి ఎప్పుడు విత్తాలి? టమోటా ఎరువుల వివరాలు...'
                  : selectedLang === 'ta'
                  ? 'எ.கா: பருத்தி விதைப்பு மாதம்? தக்காளி உர அட்டவணை...'
                  : selectedLang === 'kn'
                  ? 'ಉದಾ: ಹತ್ತಿ ಬಿತ್ತನೆ ಸಮಯ? ಗೋಧಿಗೆ ಮೊದಲ ನೀರು ಯಾವಾಗ?'
                  : selectedLang === 'mr'
                  ? 'उदा: कापूस पेरणी कधी करावी? गव्हाचे पहिले पाणी कधी द्यावे?'
                  : selectedLang === 'pa'
                  ? 'ਉਦਾ: ਕਪਾਹ ਦੀ ਬਿਜਾਈ ਕਿਸ ਮਹੀਨੇ ਕਰੀਏ? ਕਣਕ ਦਾ ਪਹਿਲਾ ਪਾਣੀ...'
                  : 'E.g. What month to sow Cotton in Maharashtra? When is Wheat CRI stage?'
              }
              className="flex-1 py-3 text-sm sm:text-base text-soil-900 placeholder:text-soil-400 focus:outline-none bg-transparent"
              disabled={loading}
            />

            {/* Voice Input Button */}
            <button
              type="button"
              onClick={toggleSpeechRecognition}
              className={`p-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition ${
                isListening
                  ? 'bg-rose-500 text-white animate-pulse'
                  : 'bg-soil-100 text-soil-700 hover:bg-forest-100 hover:text-forest-800'
              }`}
              title="Speak in your regional language"
            >
              {isListening ? (
                <>
                  <MicOff className="w-4 h-4" />
                  <span className="text-xs hidden sm:inline">Listening...</span>
                </>
              ) : (
                <>
                  <Mic className="w-4 h-4" />
                  <span className="text-xs hidden sm:inline">बोलें / Voice</span>
                </>
              )}
            </button>

            {/* Ask Button */}
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="bg-forest-700 hover:bg-forest-800 disabled:opacity-40 disabled:hover:bg-forest-700 text-white px-5 py-2.5 rounded-xl font-medium text-sm transition flex items-center gap-1.5"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <span>पूछें / Ask</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* 4. Quick Action Chips (Immediate First-Run Affordance) */}
        {!advisoryData && !loading && (
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-soil-500 text-center">
              Quick Farmer Queries (त्वरित कृषि प्रश्न)
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {quickPrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handlePromptClick(p.query)}
                  className="text-left p-3.5 rounded-xl bg-white hover:bg-soil-100/80 border border-soil-200 transition-all hover:border-forest-300 flex items-start gap-3 group"
                >
                  <span className="w-6 h-6 rounded-md bg-forest-50 text-forest-700 flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 group-hover:bg-forest-700 group-hover:text-white transition">
                    {idx + 1}
                  </span>
                  <div>
                    <h3 className="text-xs font-semibold text-forest-900">
                      {p.title}
                    </h3>
                    <p className="text-xs text-soil-600 line-clamp-1 mt-0.5">
                      {p.query}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 5. Loading State with Informative Progress */}
        {loading && (
          <div className="bg-white rounded-2xl border border-soil-200 p-6 space-y-4 shadow-sm">
            <div className="flex items-center gap-3">
              <RefreshCw className="w-5 h-5 text-forest-700 animate-spin shrink-0" />
              <div>
                <p className="text-sm font-semibold text-forest-900">
                  {executionMode === 'local_agriparam'
                    ? 'Computing with BharatGen AgriParam (2.86B) on AMD Ryzen CPU...'
                    : 'Retrieving Official ICAR Guidelines & Synthesizing Advisory...'}
                </p>
                <p className="text-xs text-soil-500">
                  {executionMode === 'local_agriparam'
                    ? 'Executing PyTorch transformer forward pass on CPU RAM (~15-25 seconds)...'
                    : 'Searching 968 indexed ICAR chunks + AI4Bharat IndicTrans2 translation...'}
                </p>
              </div>
            </div>
            <div className="space-y-2 pt-2 animate-pulse">
              <div className="h-4 bg-soil-200 rounded w-full"></div>
              <div className="h-4 bg-soil-200 rounded w-5/6"></div>
              <div className="h-4 bg-soil-200 rounded w-4/6"></div>
            </div>
          </div>
        )}

        {/* 6. Error Banner */}
        {errorMsg && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Notice</p>
              <p className="text-xs text-rose-700 mt-0.5">{errorMsg}</p>
            </div>
          </div>
        )}

        {/* 7. Advisory Output Card */}
        {advisoryData && !loading && (
          <div className="bg-white rounded-2xl border border-soil-200 shadow-sm overflow-hidden space-y-6 p-6 sm:p-8">
            {/* Advisory Header: Groundedness & Audio Read-Aloud */}
            <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-soil-100">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-forest-600"></span>
                <span className="text-xs font-semibold text-soil-700 uppercase tracking-wide">
                  Agronomic Advisory ({advisoryData.language_display})
                </span>
                <span className="text-xs px-2 py-0.5 rounded-md bg-forest-50 text-forest-700 font-medium border border-forest-200 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-forest-600" />
                  Groundedness: {Math.round(advisoryData.groundedness_score * 100)}%
                </span>
              </div>

              {/* TTS Read-Aloud Button */}
              <button
                type="button"
                onClick={() => toggleAudioReadAloud(advisoryData.advisory)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition ${
                  isPlayingAudio
                    ? 'bg-forest-700 text-white'
                    : 'bg-forest-50 text-forest-800 hover:bg-forest-100 border border-forest-200'
                }`}
                title="Listen to advisory audio in selected language"
              >
                {isPlayingAudio ? (
                  <>
                    <VolumeX className="w-4 h-4" />
                    <span>Stop Audio (रोकें)</span>
                  </>
                ) : (
                  <>
                    <Volume2 className="w-4 h-4" />
                    <span>Listen (सुनें)</span>
                  </>
                )}
              </button>
            </div>

            {/* Advisory Text Body */}
            <div className="space-y-4">
              <div className="text-sm sm:text-base leading-relaxed text-soil-900 whitespace-pre-line max-w-prose">
                {advisoryData.advisory}
              </div>
            </div>

            {/* 3-Step Action Plan */}
            {advisoryData.action_plan && advisoryData.action_plan.length > 0 && (
              <div className="pt-4 border-t border-soil-100 space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-soil-700 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-forest-600" />
                  Key Action Steps (महत्वपूर्ण चरण)
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {advisoryData.action_plan.map((step, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-soil-50 border border-soil-200 flex flex-col justify-between"
                    >
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="w-5 h-5 rounded-full bg-forest-700 text-white flex items-center justify-center text-xs font-bold">
                          {idx + 1}
                        </span>
                        <span className="text-xs font-semibold text-soil-700">
                          {idx === 0 ? 'Field Prep & Sowing' : idx === 1 ? 'Nutrient Application' : 'Irrigation & Care'}
                        </span>
                      </div>
                      <p className="text-xs text-soil-800 leading-snug">
                        {step}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Model & Source Citation Drawer */}
            <div className="pt-2 border-t border-soil-100">
              <button
                type="button"
                onClick={() => setShowSources(!showSources)}
                className="w-full py-2 flex items-center justify-between text-xs font-medium text-soil-600 hover:text-forest-700 transition"
              >
                <div className="flex items-center gap-2">
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>
                    Verified ICAR Scientific References ({advisoryData.sources.length} sources cited)
                  </span>
                </div>
                {showSources ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showSources && (
                <div className="mt-3 space-y-3 pt-2">
                  <div className="p-3 bg-soil-100 rounded-lg text-xs text-soil-700 flex items-center justify-between">
                    <span>
                      <strong>Sovereign LLM Pipeline:</strong> {advisoryData.model_engine}
                    </span>
                    <span className="text-soil-500">Latency: {advisoryData.latency_ms} ms</span>
                  </div>

                  <div className="space-y-2">
                    {advisoryData.sources.map((src, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-white border border-soil-200 text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between font-semibold text-forest-900">
                          <span>{src.source}</span>
                          <span className="text-soil-500 font-normal">
                            Confidence: {Math.round(src.confidence * 100)}%
                          </span>
                        </div>
                        <p className="text-soil-600 font-mono text-[11px] leading-relaxed">
                          {src.text_snippet}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Architecture & Model Breakdown Collapsible */}
        <div className="border-t border-soil-200 pt-4">
          <button
            type="button"
            onClick={() => setShowArchitecture(!showArchitecture)}
            className="w-full flex items-center justify-between p-3.5 rounded-xl bg-soil-100/70 hover:bg-soil-100 border border-soil-200 text-xs font-semibold text-soil-800 transition"
          >
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-forest-700" />
              <span>How This System Works (Sovereign Models & RAG Architecture)</span>
            </div>
            {showArchitecture ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showArchitecture && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
              {/* Card 1: RAG & Embeddings */}
              <div className="p-4 rounded-xl bg-white border border-soil-200 space-y-2 shadow-xs">
                <div className="flex items-center gap-2 text-forest-800 font-semibold text-xs">
                  <span className="w-5 h-5 rounded bg-forest-100 text-forest-800 flex items-center justify-center text-[10px] font-bold">1</span>
                  <span>ChromaDB RAG & MiniLM</span>
                </div>
                <p className="text-[11px] text-soil-600 leading-relaxed">
                  Indexes 968 chunks from authentic ICAR manuals & PMFBY National Crop Calendars. Encodes queries into 384-d semantic vectors to retrieve strict agronomic facts.
                </p>
                <div className="text-[10px] font-mono text-soil-500 bg-soil-50 p-1.5 rounded border border-soil-200">
                  paraphrase-multilingual-MiniLM-L12-v2
                </div>
              </div>

              {/* Card 2: IndicTrans2 Translation */}
              <div className="p-4 rounded-xl bg-white border border-soil-200 space-y-2 shadow-xs">
                <div className="flex items-center gap-2 text-harvest-800 font-semibold text-xs">
                  <span className="w-5 h-5 rounded bg-harvest-100 text-harvest-800 flex items-center justify-center text-[10px] font-bold">2</span>
                  <span>AI4Bharat IndicTrans2</span>
                </div>
                <p className="text-[11px] text-soil-600 leading-relaxed">
                  Provides 2-way translation across 7 Indian languages (Hindi, Telugu, Tamil, Kannada, Marathi, Punjabi, English) so farmers can ask and receive advice in their mother tongue.
                </p>
                <div className="text-[10px] font-mono text-soil-500 bg-soil-50 p-1.5 rounded border border-soil-200">
                  ai4bharat/indictrans2-*-dist-200M
                </div>
              </div>

              {/* Card 3: BharatGen AgriParam */}
              <div className="p-4 rounded-xl bg-white border border-soil-200 space-y-2 shadow-xs">
                <div className="flex items-center gap-2 text-emerald-800 font-semibold text-xs">
                  <span className="w-5 h-5 rounded bg-emerald-100 text-emerald-800 flex items-center justify-center text-[10px] font-bold">3</span>
                  <span>BharatGen AgriParam</span>
                </div>
                <p className="text-[11px] text-soil-600 leading-relaxed">
                  2.86B parameter sovereign LLM pre-trained by IIT Bombay / BharatGen specifically for Indian agriculture. Formulates structured, grounded advice without hallucination.
                </p>
                <div className="text-[10px] font-mono text-soil-500 bg-soil-50 p-1.5 rounded border border-soil-200">
                  bharatgenai/AgriParam (2.86B)
                </div>
              </div>
            </div>
          )}
        </div>

      </main>

      {/* 8. Institutional Footer */}
      <footer className="border-t border-soil-200 bg-white py-6 mt-auto">
        <div className="max-w-6xl mx-auto px-6 text-center text-xs text-soil-500 space-y-1">
          <p>
            AI Farmer Advisory System | Built with <strong>BharatGen AgriParam</strong>,{' '}
            <strong>AI4Bharat IndicTrans2</strong>, and <strong>ChromaDB RAG</strong>
          </p>
          <p className="text-soil-400">
            Backed by packages of practices from ICAR-CICR, ICAR-IIHR, ICAR-CRIJAF, ICAR-IIWBR, and State Agricultural Universities.
          </p>
        </div>
      </footer>
    </div>
  );
}
